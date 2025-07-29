from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from loguru import logger


@dataclass
class ToolMetadata:
    """Tool metadata structure"""
    name: str
    description: str
    category: str
    version: str
    author: str
    required_permissions: List[str]
    timeout: int = 300
    rate_limit_per_min: int = 60
    enabled: bool = True


class BaseTool(ABC):
    """Base abstract class for all MANDAS tools"""
    
    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata
        self.initialized = False
        self.execution_count = 0
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the tool with required resources"""
        pass
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass
    
    @abstractmethod
    async def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tool parameters and return validation result"""
        pass
    
    @abstractmethod
    async def get_parameter_schema(self) -> Dict[str, Any]:
        """Return OpenAPI schema for tool parameters"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check (optional override)"""
        return {
            "healthy": True,
            "tool": self.metadata.name,
            "initialized": self.initialized,
            "execution_count": self.execution_count
        }
    
    async def cleanup(self):
        """Cleanup resources (optional override)"""
        logger.info(f"Cleaning up tool: {self.metadata.name}")
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Get tool metadata and status"""
        return {
            "metadata": self.metadata.__dict__,
            "initialized": self.initialized,
            "execution_count": self.execution_count,
            "type": self.__class__.__name__
        }
    
    async def _pre_execute(self, parameters: Dict[str, Any], user_context: Dict[str, Any]):
        """Pre-execution hook"""
        self.execution_count += 1
        logger.info(f"Executing tool {self.metadata.name} (count: {self.execution_count})")
    
    async def _post_execute(self, result: Dict[str, Any], parameters: Dict[str, Any]):
        """Post-execution hook"""
        logger.info(f"Tool {self.metadata.name} execution completed: {result.get('success', False)}")
