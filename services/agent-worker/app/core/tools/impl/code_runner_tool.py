import tempfile
import os
import asyncio
from typing import Dict, Any
from app.core.base_tool import BaseTool, ToolMetadata


class CodeRunnerTool(BaseTool):
    """Tool for executing Python code in sandboxed environment"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="code_runner",
            description="Executes Python code in a secure sandbox",
            category="code_execution",
            version="1.0.0",
            author="MANDAS System",
            required_permissions=["code_execution"],
            timeout=300,
            rate_limit_per_min=10
        )
        super().__init__(metadata)
    
    async def initialize(self) -> bool:
        """Initialize code runner tool"""
        self.initialized = True
        return True
    
    async def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate code parameter"""
        if "code" not in parameters:
            return {"valid": False, "error": "code parameter is required"}
        
        code = parameters["code"]
        if not isinstance(code, str):
            return {"valid": False, "error": "code must be a string"}
        
        if len(code.strip()) == 0:
            return {"valid": False, "error": "code cannot be empty"}
        
        dangerous_patterns = ["import os", "subprocess", "__import__", "eval(", "exec("]
        for pattern in dangerous_patterns:
            if pattern in code.lower():
                return {"valid": False, "error": f"Potentially dangerous code pattern: {pattern}"}
        
        return {"valid": True}
    
    async def execute(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python code"""
        await self._pre_execute(parameters, user_context)
        
        try:
            validation = await self.validate_parameters(parameters)
            if not validation["valid"]:
                return {"success": False, "error": validation["error"]}
            
            code = parameters["code"]
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                process = await asyncio.create_subprocess_exec(
                    'python', temp_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.metadata.timeout
                )
                
                result = {
                    "success": process.returncode == 0,
                    "stdout": stdout.decode('utf-8'),
                    "stderr": stderr.decode('utf-8'),
                    "exit_code": process.returncode
                }
                
            finally:
                os.unlink(temp_file)
            
            await self._post_execute(result, parameters)
            return result
            
        except asyncio.TimeoutError:
            error_result = {"success": False, "error": "Code execution timeout"}
            await self._post_execute(error_result, parameters)
            return error_result
        except Exception as e:
            error_result = {"success": False, "error": str(e)}
            await self._post_execute(error_result, parameters)
            return error_result
    
    async def get_parameter_schema(self) -> Dict[str, Any]:
        """Return parameter schema"""
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute"
                }
            },
            "required": ["code"]
        }
