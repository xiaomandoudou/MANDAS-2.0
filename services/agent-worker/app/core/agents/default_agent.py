from typing import Dict, Any, List, Optional
from app.core.base_agent import BaseAgent
from app.core.tools.tool_registry import ToolRegistry
from app.core.logging.enhanced_logger import EnhancedLogger
from app.memory.memory_manager import MemoryManager


class DefaultAgent(BaseAgent):
    """Default agent implementation with tool selection and memory management"""
    
    def __init__(self, agent_config: Dict[str, Any], tool_registry: ToolRegistry, memory_manager: MemoryManager):
        super().__init__("DefaultAgent", agent_config)
        self.tool_registry = tool_registry
        self.memory_manager = memory_manager
        self.logger = EnhancedLogger("DefaultAgent")
        self.conversation_history: List[Dict[str, Any]] = []
    
    async def initialize(self) -> bool:
        """Initialize default agent"""
        try:
            self.logger.info("Initializing DefaultAgent")
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize DefaultAgent: {e}")
            return False
    
    async def process_task(self, task_id: str, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process task with automatic tool selection"""
        with self.logger.trace_context(task_id=task_id) as trace_id:
            self.logger.info(f"Processing task: {task_id}")
            
            try:
                memory_context = await self.memory_manager.get_context_for_llm(prompt, task_id)
                
                required_tools = await self._analyze_prompt_for_tools(prompt)
                
                result = await self._execute_with_tools(task_id, prompt, required_tools, context)
                
                await self._store_conversation(task_id, prompt, result)
                
                self.logger.log_agent_action(
                    self.name, 
                    "task_completed", 
                    {"task_id": task_id, "success": result.get("success", False)}
                )
                
                return result
                
            except Exception as e:
                self.logger.error(f"Error processing task {task_id}: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "task_id": task_id
                }
    
    async def _analyze_prompt_for_tools(self, prompt: str) -> List[str]:
        """Analyze prompt to determine required tools"""
        prompt_lower = prompt.lower()
        required_tools = []
        
        if any(keyword in prompt_lower for keyword in ["read", "file", "open", "load"]):
            required_tools.append("file_reader")
        
        if any(keyword in prompt_lower for keyword in ["code", "python", "execute", "run", "script"]):
            required_tools.append("code_runner")
        
        return required_tools
    
    async def _execute_with_tools(self, task_id: str, prompt: str, tool_names: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using selected tools"""
        results = []
        
        for tool_name in tool_names:
            if tool_name in self.tool_registry.tool_instances:
                parameters = await self._extract_tool_parameters(prompt, tool_name)
                
                tool_result = await self.tool_registry.execute_tool(
                    tool_name, 
                    parameters, 
                    {"task_id": task_id, **context}
                )
                
                results.append({
                    "tool": tool_name,
                    "result": tool_result
                })
                
                self.logger.log_tool_execution(tool_name, parameters, tool_result)
        
        if results:
            return {
                "success": True,
                "results": results,
                "summary": self._generate_summary(results),
                "task_id": task_id
            }
        else:
            return {
                "success": True,
                "message": f"Processed prompt: {prompt}",
                "task_id": task_id
            }
    
    async def _extract_tool_parameters(self, prompt: str, tool_name: str) -> Dict[str, Any]:
        """Extract tool parameters from prompt (simplified implementation)"""
        if tool_name == "file_reader":
            words = prompt.split()
            for word in words:
                if word.endswith(('.txt', '.py', '.json', '.yaml', '.md')):
                    return {"file_path": word}
            return {"file_path": "/tmp/example.txt"}
        
        elif tool_name == "code_runner":
            if "```python" in prompt:
                start = prompt.find("```python") + 9
                end = prompt.find("```", start)
                if end > start:
                    return {"code": prompt[start:end].strip()}
            return {"code": "print('Hello from DefaultAgent!')"}
        
        return {}
    
    def _generate_summary(self, results: List[Dict[str, Any]]) -> str:
        """Generate summary from tool execution results"""
        successful_tools = [r for r in results if r["result"].get("success", False)]
        
        if successful_tools:
            return f"Successfully executed {len(successful_tools)} tools: {', '.join([r['tool'] for r in successful_tools])}"
        else:
            return "Task completed but no tools were successfully executed"
    
    async def _store_conversation(self, task_id: str, prompt: str, result: Dict[str, Any]):
        """Store conversation in memory"""
        conversation = [
            {"role": "user", "content": prompt, "name": "User"},
            {"role": "assistant", "content": result.get("summary", "Task completed"), "name": self.name}
        ]
        
        await self.memory_manager.store_conversation(task_id, conversation)
    
    async def get_capabilities(self) -> List[str]:
        """Return agent capabilities"""
        return [
            "task_processing",
            "tool_selection",
            "memory_management",
            "conversation_storage"
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "healthy": True,
            "agent": self.name,
            "initialized": self.initialized,
            "available_tools": len(self.tool_registry.tool_instances),
            "memory_connected": self.memory_manager.redis_client is not None
        }
