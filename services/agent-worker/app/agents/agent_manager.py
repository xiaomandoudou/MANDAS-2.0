import asyncio
from typing import Dict, Any, List
from loguru import logger
import autogen
from autogen import UserProxyAgent, AssistantAgent, GroupChatManager, GroupChat

from app.core.config import settings
from app.llm.llm_router import LLMRouter
from app.tools.tool_executor import ToolExecutor
from app.memory.memory_manager import MemoryManager


class AgentManager:
    def __init__(self):
        self.llm_router = None
        self.tool_executor = None
        self.memory_manager = None
        self.agents = {}

    async def initialize(self):
        self.llm_router = LLMRouter()
        self.tool_executor = ToolExecutor()
        self.memory_manager = MemoryManager()
        
        await self.llm_router.initialize()
        await self.tool_executor.initialize()
        await self.memory_manager.initialize()
        
        await self.setup_agents()
        logger.info("Agent Manager initialized successfully")

    async def setup_agents(self):
        llm_config = await self.llm_router.get_default_config()
        
        self.agents["user_proxy"] = UserProxyAgent(
            name="UserProxy",
            system_message="你是一个用户代理，负责执行代码和工具调用。你可以安全地在Docker容器中执行Python代码和Shell命令。",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            code_execution_config={
                "work_dir": "/tmp/agent_workspace",
                "use_docker": True,
                "timeout": 300,
            },
            llm_config=llm_config,
        )
        
        self.agents["planner"] = AssistantAgent(
            name="Planner",
            system_message="""你是一个智能任务规划者。你的职责是：
1. 分析用户的任务需求
2. 制定详细的执行计划
3. 将复杂任务分解为可执行的步骤
4. 选择合适的工具和方法
5. 与执行者协作完成任务

请始终用中文回复，并确保计划清晰、可执行。""",
            llm_config=llm_config,
        )
        
        self.agents["reviewer"] = AssistantAgent(
            name="Reviewer",
            system_message="""你是一个质量审查者。你的职责是：
1. 检查任务执行结果的质量
2. 验证输出是否符合要求
3. 提出改进建议
4. 确保最终结果的准确性

请始终用中文回复，并提供建设性的反馈。""",
            llm_config=llm_config,
        )

    async def process_task(self, task_id: str, prompt: str, config: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Processing task {task_id} with Agent Manager")
        
        try:
            context = await self.memory_manager.get_relevant_context(prompt)
            
            enhanced_prompt = f"""
任务ID: {task_id}
用户需求: {prompt}

相关上下文:
{context}

请分析这个任务，制定执行计划，并完成任务。
"""
            
            agents = [
                self.agents["user_proxy"],
                self.agents["planner"],
                self.agents["reviewer"]
            ]
            
            group_chat = GroupChat(
                agents=agents,
                messages=[],
                max_round=20,
                speaker_selection_method="round_robin"
            )
            
            manager = GroupChatManager(
                groupchat=group_chat,
                llm_config=await self.llm_router.get_default_config()
            )
            
            result = await asyncio.to_thread(
                self.agents["user_proxy"].initiate_chat,
                manager,
                message=enhanced_prompt
            )
            
            conversation_history = []
            for msg in group_chat.messages:
                conversation_history.append({
                    "role": msg.get("role", "unknown"),
                    "name": msg.get("name", "unknown"),
                    "content": msg.get("content", "")
                })
            
            await self.memory_manager.store_conversation(task_id, conversation_history)
            
            final_result = {
                "status": "success",
                "conversation": conversation_history,
                "summary": self.extract_final_answer(conversation_history),
                "task_id": task_id
            }
            
            logger.info(f"Task {task_id} completed successfully")
            return final_result
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "task_id": task_id
            }

    def extract_final_answer(self, conversation: List[Dict[str, Any]]) -> str:
        if not conversation:
            return "任务完成，但没有生成具体结果。"
        
        last_messages = conversation[-3:]
        
        for msg in reversed(last_messages):
            if msg.get("name") == "Reviewer" and msg.get("content"):
                return msg["content"]
        
        if conversation:
            return conversation[-1].get("content", "任务已完成。")
        
        return "任务已完成。"
