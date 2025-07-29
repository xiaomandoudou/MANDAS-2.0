import docker
import asyncio
import tempfile
import os
from typing import Dict, Any, Optional
from loguru import logger
from dataclasses import dataclass

from app.core.config import settings
from app.core.tools.tool_registry import ToolRegistry


@dataclass
class ContainerLimits:
    memory: str = "512m"
    cpu_quota: int = 50000  # 0.5 CPU
    timeout: int = 300
    network_disabled: bool = True


class DockerSandbox:
    
    def __init__(self):
        self.docker_client = None
        self.active_containers = {}
    
    async def initialize(self):
        try:
            try:
                self.docker_client = docker.from_env()
                logger.info("Docker Sandbox initialized successfully")
            except Exception as docker_error:
                logger.warning(f"Docker client initialization failed: {docker_error}")
                logger.warning("Continuing without Docker isolation - security features limited")
                self.docker_client = None
        except Exception as e:
            logger.error(f"Failed to initialize Docker sandbox: {e}")
            logger.warning("Continuing with minimal security functionality")
            self.docker_client = None
    
    async def create_container(self, task_id: str, limits: ContainerLimits) -> str:
        try:
            container = self.docker_client.containers.create(
                image=settings.docker_image_python,
                command="sleep infinity",
                labels={"mandas.task_id": task_id, "mandas.execution_guard": "true"},
                working_dir="/workspace",
                volumes={"/tmp": {"bind": "/workspace", "mode": "rw"}},
                detach=True,
                mem_limit=limits.memory,
                nano_cpus=int(0.5 * 1e9),
                network_mode='none' if limits.network_disabled else 'bridge',
                auto_remove=True
            )
            
            container.start()
            self.active_containers[task_id] = container
            logger.info(f"Created container {container.id} for task {task_id}")
            return container.id
            
        except Exception as e:
            logger.error(f"Failed to create container for task {task_id}: {e}")
            raise
    
    async def execute_in_container(self, task_id: str, command: str, timeout: int = 300) -> Dict[str, Any]:
        container = self.active_containers.get(task_id)
        if not container:
            raise ValueError(f"No container found for task {task_id}")
        
        try:
            if command.startswith('python -c'):
                shell_command = f'/bin/bash -c "{command}"'
            else:
                shell_command = f'/bin/bash -c "{command}"'
            
            result = container.exec_run(
                shell_command,
                stdout=True,
                stderr=True
            )
            
            stdout = result.output.decode('utf-8') if result.output else ""
            
            return {
                "exit_code": result.exit_code,
                "stdout": stdout,
                "stderr": ""
            }
            
        except Exception as e:
            logger.error(f"Execution failed in container for task {task_id}: {e}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    async def cleanup_container(self, task_id: str):
        container = self.active_containers.get(task_id)
        if container:
            try:
                container.stop(timeout=10)
                container.remove()
                del self.active_containers[task_id]
                logger.info(f"Cleaned up container for task {task_id}")
            except Exception as e:
                logger.error(f"Failed to cleanup container for task {task_id}: {e}")


class ExecutionGuard:
    
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self.docker_sandbox = DockerSandbox()
        self.security_policies = {
            "max_execution_time": 600,
            "max_memory": "1g",
            "allowed_networks": [],
            "blocked_commands": ["rm -rf", "sudo", "su"]
        }
    
    async def initialize(self):
        try:
            await self.docker_sandbox.initialize()
            logger.info("Execution Guard initialized successfully")
        except Exception as e:
            logger.warning(f"Execution Guard initialization with limited functionality: {e}")
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            has_permission = await self.tool_registry.check_permission(tool_name, user_context)
            if not has_permission:
                return {
                    "success": False,
                    "error": f"Permission denied for tool '{tool_name}'"
                }
            
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found"
                }
            
            security_check = await self._security_check(tool_name, parameters)
            if not security_check["allowed"]:
                return {
                    "success": False,
                    "error": f"Security policy violation: {security_check['reason']}"
                }
            
            if tool.category in ["code_execution", "system"] and self.docker_sandbox.docker_client is not None:
                return await self._execute_in_sandbox(tool_name, parameters, user_context)
            else:
                return await self._execute_direct(tool_name, parameters, user_context)
                
        except Exception as e:
            logger.error(f"Error in ExecutionGuard.execute_tool: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _security_check(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if "command" in parameters:
            command = parameters["command"].lower()
            for blocked in self.security_policies["blocked_commands"]:
                if blocked in command:
                    return {
                        "allowed": False,
                        "reason": f"Blocked command detected: {blocked}"
                    }
        
        if "code" in parameters:
            code = parameters["code"].lower()
            dangerous_patterns = ["import os", "subprocess", "__import__"]
            for pattern in dangerous_patterns:
                if pattern in code:
                    logger.warning(f"Potentially dangerous code pattern detected: {pattern}")
        
        return {"allowed": True, "reason": ""}
    
    async def _execute_in_sandbox(self, tool_name: str, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        task_id = user_context.get("task_id", "unknown")
        
        try:
            limits = ContainerLimits(
                memory=self.security_policies["max_memory"],
                timeout=self.security_policies["max_execution_time"]
            )
            
            container_id = await self.docker_sandbox.create_container(task_id, limits)
            
            if tool_name == "python_executor":
                code = parameters.get('code', '')
                if code.strip():
                    command = f"cat > /tmp/code.py << 'EOF'\n{code}\nEOF\npython /tmp/code.py"
                else:
                    command = "python -c \"print('No code provided')\""
            elif tool_name == "shell_executor":
                command = parameters.get("command", "")
            else:
                command = f"echo 'Tool {tool_name} executed'"
            
            result = await self.docker_sandbox.execute_in_container(
                task_id, command, limits.timeout
            )
            
            try:
                await self.docker_sandbox.cleanup_container(task_id)
            except Exception as cleanup_error:
                logger.warning(f"Container cleanup failed for task {task_id}: {cleanup_error}")
            
            return {
                "success": result["exit_code"] == 0,
                "result": result["stdout"],
                "error": result["stderr"] if result["exit_code"] != 0 else None,
                "tool": tool_name
            }
            
        except Exception as e:
            try:
                await self.docker_sandbox.cleanup_container(task_id)
            except Exception as cleanup_error:
                logger.warning(f"Container cleanup failed for task {task_id}: {cleanup_error}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }
    
    async def _execute_direct(self, tool_name: str, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "echo":
            return {
                "success": True,
                "result": f"Echo: {parameters.get('text', '')}",
                "tool": tool_name
            }
        
        return {
            "success": False,
            "error": f"Direct execution not implemented for tool '{tool_name}'",
            "tool": tool_name
        }
