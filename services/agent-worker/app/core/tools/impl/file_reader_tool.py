import os
from typing import Dict, Any
from app.core.base_tool import BaseTool, ToolMetadata


class FileReaderTool(BaseTool):
    """Tool for reading file contents asynchronously"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="file_reader",
            description="Reads the content of a local file",
            category="file_system",
            version="1.0.0",
            author="MANDAS System",
            required_permissions=["file_access"],
            timeout=60,
            rate_limit_per_min=30
        )
        super().__init__(metadata)
    
    async def initialize(self) -> bool:
        """Initialize file reader tool"""
        self.initialized = True
        return True
    
    async def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate file path parameter"""
        if "file_path" not in parameters:
            return {"valid": False, "error": "file_path parameter is required"}
        
        file_path = parameters["file_path"]
        if not isinstance(file_path, str):
            return {"valid": False, "error": "file_path must be a string"}
        
        if not os.path.exists(file_path):
            return {"valid": False, "error": f"File does not exist: {file_path}"}
        
        return {"valid": True}
    
    async def execute(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file reading"""
        await self._pre_execute(parameters, user_context)
        
        try:
            validation = await self.validate_parameters(parameters)
            if not validation["valid"]:
                return {"success": False, "error": validation["error"]}
            
            file_path = parameters["file_path"]
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = {
                "success": True,
                "content": content,
                "file_path": file_path,
                "file_size": len(content)
            }
            
            await self._post_execute(result, parameters)
            return result
            
        except Exception as e:
            error_result = {"success": False, "error": str(e)}
            await self._post_execute(error_result, parameters)
            return error_result
    
    async def get_parameter_schema(self) -> Dict[str, Any]:
        """Return parameter schema"""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read"
                }
            },
            "required": ["file_path"]
        }
