from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from loguru import logger


class BaseAgent(ABC):
    """Base abstract class for all MANDAS agents"""
    
    def __init__(self, name: str, agent_config: Dict[str, Any]):
        self.name = name
        self.agent_config = agent_config
        self.initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the agent with required resources"""
        pass
    
    @abstractmethod
    async def process_task(self, task_id: str, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task and return results"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status"""
        pass
    
    async def cleanup(self):
        """Cleanup resources (optional override)"""
        logger.info(f"Cleaning up agent: {self.name}")
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent metadata"""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "initialized": self.initialized,
            "config": self.agent_config
        }
