import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger
try:
    from autogen_agentchat.agents import UserProxyAgent, AssistantAgent
    from autogen_agentchat.teams import RoundRobinGroupChat
except ImportError:
    from autogen import UserProxyAgent, AssistantAgent
    from autogen import GroupChat as RoundRobinGroupChat

from app.core.config import settings
from app.core.tools.tool_registry import ToolRegistry
from app.core.security.execution_guard import ExecutionGuard
from app.memory.memory_manager import MemoryManager
from app.core.planning.planner import TaskPlanner
from app.llm.llm_router import LLMRouter


class PlannerAgent(AssistantAgent):
    """规划者Agent - 负责任务分析、规划和分解"""
    
    def __init__(self, llm_config: Dict[str, Any], task_planner: TaskPlanner, tool_registry: ToolRegistry):
        self.task_planner = task_planner
        self.tool_registry = tool_registry
        
        system_message = """你是一个智能任务规划者(Planner)。你的核心职责是：

1. **任务分析**: 深入理解用户需求，识别任务的核心目标和约束条件
2. **制定计划**: 将复杂任务分解为清晰、可执行的步骤序列
3. **资源评估**: 评估所需的工具、权限和执行环境
4. **风险识别**: 识别潜在的执行风险和异常情况
5. **协作指导**: 为执行者提供清晰的指导和反馈

**重要原则**:
- 你只负责规划和指导，不执行具体的代码或工具调用
- 始终用中文进行交流
- 确保计划具有可操作性和可验证性
- 在不确定时主动询问澄清
- 持续监控执行进度并适时调整计划

请根据任务需求制定详细的执行计划。"""

        super().__init__(
            name="Planner",
            system_message=system_message,
            llm_config=llm_config,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10
        )
    
    async def create_task_plan(self, task_description: str, task_id: str):
        """Create a structured task plan using TaskPlanner"""
        try:
            available_tools = [tool.name for tool in self.tool_registry.list_tools(enabled_only=True)]
            plan = await self.task_planner.create_plan(task_description, available_tools, task_id)
            return plan
        except Exception as e:
            logger.error(f"Failed to create task plan: {e}")
            return None
    
    async def regenerate_task_plan(self, task_id: str, task_description: str, current_version: str = "v1"):
        """Regenerate a task plan with new version"""
        try:
            available_tools = [tool.name for tool in self.tool_registry.list_tools(enabled_only=True)]
            plan = await self.task_planner.regenerate_plan(task_id, task_description, available_tools, current_version)
            return plan
        except Exception as e:
            logger.error(f"Failed to regenerate task plan: {e}")
            return None


class EnhancedUserProxyAgent(UserProxyAgent):
    """增强的用户代理Agent - 负责代码执行和工具调用"""
    
    def __init__(self, llm_config: Dict[str, Any], tool_registry: ToolRegistry, execution_guard: ExecutionGuard):
        self.tool_registry = tool_registry
        self.execution_guard = execution_guard
        
        system_message = """你是一个执行者代理(UserProxy)。你的核心职责是：

1. **代码执行**: 在安全的Docker环境中执行Python代码和Shell命令
2. **工具调用**: 调用已注册的工具来完成特定任务
3. **结果验证**: 验证执行结果的正确性和完整性
4. **错误处理**: 处理执行过程中的异常和错误
5. **状态报告**: 及时报告执行状态和结果

**安全原则**:
- 所有代码执行都在隔离的Docker容器中进行
- 严格遵守工具的权限和使用限制
- 对敏感操作进行额外的安全检查
- 及时清理临时文件和资源

请根据规划者的指导执行具体任务。"""

        super().__init__(
            name="UserProxy",
            system_message=system_message,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            code_execution_config={
                "work_dir": "/tmp/agent_workspace",
                "use_docker": True,
                "timeout": 300,
            },
            llm_config=llm_config,
        )
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        try:
            has_permission = await self.tool_registry.check_permission(tool_name, user_context)
            if not has_permission:
                return {
                    "success": False,
                    "error": f"没有权限使用工具 '{tool_name}'"
                }
            
            result = await self.execution_guard.execute_tool(tool_name, parameters, user_context)
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class ReviewerAgent(AssistantAgent):
    """审查者Agent - 负责质量检查和结果验证"""
    
    def __init__(self, llm_config: Dict[str, Any]):
        system_message = """你是一个质量审查者(Reviewer)。你的核心职责是：

1. **结果验证**: 检查任务执行结果是否符合预期目标
2. **质量评估**: 评估输出的准确性、完整性和可用性
3. **改进建议**: 提出具体的改进建议和优化方案
4. **风险评估**: 识别结果中的潜在问题和风险
5. **最终确认**: 确认任务是否达到完成标准

**评审标准**:
- 功能正确性: 是否实现了预期功能
- 代码质量: 代码是否规范、可读、可维护
- 安全性: 是否存在安全隐患
- 性能: 是否满足性能要求
- 用户体验: 是否满足用户需求

请对执行结果进行全面的质量审查。"""

        super().__init__(
            name="Reviewer",
            system_message=system_message,
            llm_config=llm_config,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10
        )


class MandasGroupChatManager:
    """Mandas多Agent协同管理器"""
    
    def __init__(self, tool_registry: ToolRegistry, execution_guard: ExecutionGuard, memory_manager: MemoryManager, llm_router: LLMRouter):
        self.tool_registry = tool_registry
        self.execution_guard = execution_guard
        self.memory_manager = memory_manager
        self.llm_router = llm_router
        self.task_planner = TaskPlanner(llm_router)
        self.agents = {}
        self.group_chat = None
        self.manager = None
    
    async def initialize(self, llm_config: Dict[str, Any]):
        """初始化Agent群组"""
        try:
            self.llm_config = llm_config
            
            self.agents["planner"] = PlannerAgent(llm_config, self.task_planner, self.tool_registry)
            self.agents["user_proxy"] = EnhancedUserProxyAgent(
                llm_config, self.tool_registry, self.execution_guard
            )
            self.agents["reviewer"] = ReviewerAgent(llm_config)
            
            agents_list = [
                self.agents["user_proxy"],
                self.agents["planner"], 
                self.agents["reviewer"]
            ]
            
            self.group_chat = RoundRobinGroupChat(
                agents=agents_list,
                messages=[],
                max_round=settings.max_agent_rounds
            )
            
            logger.info("Group Chat Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Group Chat Manager: {e}")
            raise
    
    async def process_task(self, task_id: str, prompt: str, config: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务 - 启动多Agent协同会话"""
        try:
            logger.info(f"Starting multi-agent collaboration for task {task_id}")
            
            if self.group_chat is None:
                logger.error(f"Group chat not initialized for task {task_id}")
                return {
                    "status": "error",
                    "error": "Group chat not initialized",
                    "task_id": task_id
                }
            
            context = await self.memory_manager.get_context_for_llm(prompt, task_id)
            
            enhanced_prompt = self._build_enhanced_prompt(task_id, prompt, context, config)
            
            if hasattr(self.group_chat, 'messages'):
                self.group_chat.messages = []
            
            from autogen import GroupChatManager
            
            group_chat_manager = GroupChatManager(
                groupchat=self.group_chat,
                llm_config=self.llm_config
            )
            
            result = await asyncio.to_thread(
                group_chat_manager.initiate_chat,
                self.agents["planner"],
                message=enhanced_prompt
            )
            
            conversation_history = self._extract_conversation_history()
            
            await self.memory_manager.store_conversation(task_id, conversation_history)
            
            final_result = self._analyze_final_result(conversation_history, task_id)
            
            completion_status = self._check_completion_status(conversation_history)
            
            result_data = {
                "status": "success" if completion_status["completed"] else "partial",
                "conversation": conversation_history,
                "summary": final_result,
                "completion_details": completion_status,
                "task_id": task_id,
                "agent_stats": self._get_agent_statistics(conversation_history)
            }
            
            logger.info(f"Multi-agent collaboration completed for task {task_id}")
            return result_data
            
        except Exception as e:
            logger.error(f"Error in multi-agent collaboration for task {task_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "task_id": task_id
            }
    
    def _build_enhanced_prompt(self, task_id: str, prompt: str, context: str, config: Dict[str, Any]) -> str:
        """构建增强的任务提示"""
        available_tools = self.tool_registry.list_tools(enabled_only=True)
        tools_info = "\n".join([f"- {tool.name}: {tool.description}" for tool in available_tools[:10]])
        
        enhanced_prompt = f"""

**任务ID**: {task_id}
**用户需求**: {prompt}

{tools_info}

{context}

优先级: {config.get('priority', 5)}
超时时间: {config.get('timeout', 300)}秒
特殊要求: {config.get('special_requirements', '无')}

1. **Planner**: 请首先分析任务需求，制定详细的执行计划
2. **UserProxy**: 根据计划执行具体的代码和工具调用
3. **Reviewer**: 对执行结果进行质量检查和验证

请开始协作完成这个任务。
"""
        return enhanced_prompt
    
    def _extract_conversation_history(self) -> List[Dict[str, Any]]:
        """提取对话历史"""
        conversation = []
        if self.group_chat and hasattr(self.group_chat, 'messages') and self.group_chat.messages:
            for msg in self.group_chat.messages:
                conversation.append({
                    "role": msg.get("role", "unknown"),
                    "name": msg.get("name", "unknown"),
                    "content": msg.get("content", ""),
                    "timestamp": msg.get("timestamp", "")
                })
        return conversation
    
    def _analyze_final_result(self, conversation: List[Dict[str, Any]], task_id: str) -> str:
        """分析最终结果"""
        if not conversation:
            return "任务执行完成，但没有生成对话记录。"
        
        reviewer_messages = [msg for msg in conversation if msg.get("name") == "Reviewer"]
        if reviewer_messages:
            last_review = reviewer_messages[-1].get("content", "")
            if "完成" in last_review or "成功" in last_review:
                return last_review
        
        proxy_messages = [msg for msg in conversation if msg.get("name") == "UserProxy"]
        if proxy_messages:
            last_execution = proxy_messages[-1].get("content", "")
            return f"执行结果: {last_execution}"
        
        if conversation:
            return conversation[-1].get("content", "任务已处理完成。")
        
        return "任务已完成。"
    
    def _check_completion_status(self, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检查任务完成状态"""
        completion_indicators = ["完成", "成功", "结束", "done", "finished", "completed"]
        error_indicators = ["错误", "失败", "异常", "error", "failed", "exception"]
        
        completed = False
        has_errors = False
        
        for msg in conversation:
            content = msg.get("content", "").lower()
            
            if any(indicator in content for indicator in completion_indicators):
                completed = True
            
            if any(indicator in content for indicator in error_indicators):
                has_errors = True
        
        return {
            "completed": completed,
            "has_errors": has_errors,
            "total_messages": len(conversation),
            "termination_reason": self._determine_termination_reason(conversation)
        }
    
    def _determine_termination_reason(self, conversation: List[Dict[str, Any]]) -> str:
        """确定终止原因"""
        if not conversation:
            return "no_conversation"
        
        last_msg = conversation[-1].get("content", "").lower()
        
        if "完成" in last_msg or "成功" in last_msg:
            return "task_completed"
        elif "错误" in last_msg or "失败" in last_msg:
            return "error_occurred"
        elif len(conversation) >= settings.max_agent_rounds:
            return "max_rounds_reached"
        else:
            return "normal_termination"
    
    def _get_agent_statistics(self, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取Agent统计信息"""
        stats = {
            "total_messages": len(conversation),
            "agent_participation": {},
            "message_distribution": {}
        }
        
        for msg in conversation:
            agent_name = msg.get("name", "unknown")
            if agent_name not in stats["agent_participation"]:
                stats["agent_participation"][agent_name] = 0
            stats["agent_participation"][agent_name] += 1
        
        total = len(conversation)
        if total > 0:
            for agent, count in stats["agent_participation"].items():
                stats["message_distribution"][agent] = round((count / total) * 100, 2)
        
        return stats
