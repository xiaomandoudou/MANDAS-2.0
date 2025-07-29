import docker
import asyncio
import json
import tempfile
import os
from typing import Dict, Any, List
from loguru import logger

from app.core.config import settings


class ToolExecutor:
    def __init__(self):
        self.docker_client = None
        self.available_tools = {}

    async def initialize(self):
        try:
            self.docker_client = docker.from_env()
            await self.register_default_tools()
            logger.info("Tool Executor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise

    async def register_default_tools(self):
        self.available_tools = {
            "echo": self.echo_tool,
            "python_executor": self.python_executor,
            "shell_executor": self.shell_executor,
        }
        logger.info(f"Registered tools: {list(self.available_tools.keys())}")

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self.available_tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(self.available_tools.keys())
            }
        
        try:
            result = await self.available_tools[tool_name](parameters)
            return {
                "success": True,
                "result": result,
                "tool": tool_name
            }
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }

    async def echo_tool(self, parameters: Dict[str, Any]) -> str:
        text = parameters.get("text", "")
        logger.info(f"Echo tool called with: {text}")
        return f"Echo: {text}"

    async def python_executor(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        code = parameters.get("code", "")
        if not code:
            return {"error": "No code provided"}
        
        logger.info(f"Executing Python code in Docker container")
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                container = self.docker_client.containers.run(
                    settings.docker_image_python,
                    command=f"python /tmp/script.py",
                    volumes={temp_file: {'bind': '/tmp/script.py', 'mode': 'ro'}},
                    remove=True,
                    detach=False,
                    stdout=True,
                    stderr=True,
                    timeout=60,
                    mem_limit="512m",
                    network_disabled=True
                )
                
                output = container.decode('utf-8')
                return {
                    "output": output,
                    "exit_code": 0
                }
                
            finally:
                os.unlink(temp_file)
                
        except docker.errors.ContainerError as e:
            return {
                "error": f"Container execution failed: {e.stderr.decode('utf-8')}",
                "exit_code": e.exit_status
            }
        except Exception as e:
            return {
                "error": f"Execution failed: {str(e)}",
                "exit_code": -1
            }

    async def shell_executor(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        command = parameters.get("command", "")
        if not command:
            return {"error": "No command provided"}
        
        logger.info(f"Executing shell command in Docker container: {command}")
        
        try:
            container = self.docker_client.containers.run(
                settings.docker_image_ubuntu,
                command=f"bash -c '{command}'",
                remove=True,
                detach=False,
                stdout=True,
                stderr=True,
                timeout=60,
                mem_limit="512m",
                network_disabled=True
            )
            
            output = container.decode('utf-8')
            return {
                "output": output,
                "exit_code": 0
            }
            
        except docker.errors.ContainerError as e:
            return {
                "error": f"Container execution failed: {e.stderr.decode('utf-8')}",
                "exit_code": e.exit_status
            }
        except Exception as e:
            return {
                "error": f"Execution failed: {str(e)}",
                "exit_code": -1
            }

    def get_available_tools(self) -> List[str]:
        return list(self.available_tools.keys())

    async def cleanup(self):
        if self.docker_client:
            try:
                containers = self.docker_client.containers.list(
                    filters={"label": "mandas.tool_executor"}
                )
                for container in containers:
                    container.stop()
                    container.remove()
                logger.info("Cleaned up Docker containers")
            except Exception as e:
                logger.error(f"Error cleaning up containers: {e}")
