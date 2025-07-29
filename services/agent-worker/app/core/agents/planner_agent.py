# services/agent-worker/app/core/agents/planner_agent.py

from typing import Dict, Any, Optional
from datetime import datetime

from app.core.base_agent import BaseAgent
from app.core.planning.planner import TaskPlanner, TaskPlan
from app.core.logging.enhanced_logger import EnhancedLogger


class PlannerAgent(BaseAgent):
    """
    规划代理，其核心职责是使用TaskPlanner生成计划。
    这是MANDAS V1.3版本引入的智能规划系统的核心组件。
    """

    def __init__(self, llm_client, config: Optional[Dict] = None):
        """
        初始化PlannerAgent
        
        Args:
            llm_client: LLM客户端实例
            config: 代理配置字典
        """
        super().__init__(config or {})
        self.name = "PlannerAgent"
        self.llm_client = llm_client
        self.planner = TaskPlanner(llm_client)
        self.logger = EnhancedLogger("PlannerAgent")
        
        # 配置参数
        self.max_retry_attempts = config.get("max_retry_attempts", 3) if config else 3
        self.enable_plan_optimization = config.get("enable_plan_optimization", True) if config else True
        
        self.logger.info("PlannerAgent initialized", extra_data={
            "max_retry_attempts": self.max_retry_attempts,
            "enable_plan_optimization": self.enable_plan_optimization
        })

    async def initialize(self):
        """初始化代理"""
        try:
            self.logger.info("Initializing PlannerAgent")
            # 这里可以添加初始化逻辑，比如加载配置、连接数据库等
            self.initialized = True
            self.logger.info("PlannerAgent initialization completed")
        except Exception as e:
            self.logger.error(f"PlannerAgent initialization failed: {e}")
            raise

    async def get_capabilities(self) -> Dict[str, Any]:
        """返回代理的能力描述"""
        return {
            "task_planning": True,
            "dependency_analysis": True,
            "plan_validation": True,
            "plan_optimization": self.enable_plan_optimization,
            "supported_formats": ["natural_language", "structured_json"],
            "max_plan_complexity": 50,  # 最大支持50个步骤
            "retry_mechanism": True
        }

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查LLM客户端状态
            llm_healthy = hasattr(self.llm_client, 'generate') and callable(self.llm_client.generate)
            
            return {
                "healthy": self.initialized and llm_healthy,
                "agent": self.name,
                "initialized": self.initialized,
                "llm_client_available": llm_healthy,
                "planner_ready": self.planner is not None,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务规划的核心逻辑
        
        Args:
            task_input: 包含任务信息的字典
                - task_id: 任务ID
                - prompt: 用户的自然语言任务描述
                - available_tools: 可用工具列表（可选）
                - context: 额外的上下文信息（可选）
        
        Returns:
            包含生成计划的字典
        """
        task_id = task_input.get("task_id")
        prompt = task_input.get("prompt")
        available_tools = task_input.get("available_tools")
        context = task_input.get("context", {})
        
        if not task_id:
            raise ValueError("task_id is required")
        
        if not prompt:
            raise ValueError("prompt is required")

        try:
            with self.logger.trace_context(task_id=task_id) as trace_id:
                self.logger.info("Starting task planning process", extra_data={
                    "task_id": task_id,
                    "prompt_length": len(prompt),
                    "has_available_tools": available_tools is not None,
                    "context_keys": list(context.keys()) if context else []
                })

                # 更新记忆 - 记录用户输入
                if hasattr(self, 'memory_manager') and self.memory_manager:
                    await self.memory_manager.remember(
                        task_id,
                        {
                            "role": "user",
                            "content": prompt,
                            "name": "User",
                            "timestamp": datetime.now().isoformat()
                        }
                    )

                # 尝试生成计划，支持重试机制
                plan = None
                last_error = None
                
                for attempt in range(self.max_retry_attempts):
                    try:
                        self.logger.info(f"Planning attempt {attempt + 1}/{self.max_retry_attempts}")
                        
                        # 调用TaskPlanner生成计划
                        plan = await self.planner.create_plan(
                            task_description=prompt,
                            task_id=task_id,
                            available_tools=available_tools
                        )
                        
                        self.logger.info("Task plan generated successfully", extra_data={
                            "plan_id": plan.plan_id,
                            "steps_count": len(plan.steps),
                            "attempt": attempt + 1
                        })
                        
                        break  # 成功生成计划，跳出重试循环
                        
                    except Exception as e:
                        last_error = e
                        self.logger.warning(f"Planning attempt {attempt + 1} failed: {e}")
                        
                        if attempt == self.max_retry_attempts - 1:
                            # 最后一次尝试失败
                            self.logger.error("All planning attempts failed", extra_data={
                                "final_error": str(last_error),
                                "attempts": self.max_retry_attempts
                            })
                            raise last_error

                # 如果启用了计划优化，进行优化处理
                if self.enable_plan_optimization and plan:
                    plan = await self._optimize_plan(plan)

                # 更新记忆 - 记录生成的计划
                if hasattr(self, 'memory_manager') and self.memory_manager:
                    await self.memory_manager.remember(
                        task_id,
                        {
                            "role": "assistant",
                            "content": f"已为您生成包含 {len(plan.steps)} 个步骤的执行计划。计划ID: {plan.plan_id}",
                            "name": "PlannerAgent",
                            "timestamp": datetime.now().isoformat(),
                            "metadata": {
                                "plan_id": plan.plan_id,
                                "steps_count": len(plan.steps)
                            }
                        }
                    )

                # 记录规划成功的日志
                self.logger.log_agent_action(
                    agent_name=self.name,
                    action="create_plan",
                    details={
                        "task_id": task_id,
                        "plan_id": plan.plan_id,
                        "steps_count": len(plan.steps),
                        "success": True
                    }
                )

                # 返回计划结果
                return {
                    "success": True,
                    "plan": plan.model_dump(),
                    "plan_id": plan.plan_id,
                    "steps_count": len(plan.steps),
                    "message": f"成功生成包含 {len(plan.steps)} 个步骤的执行计划",
                    "trace_id": trace_id
                }

        except Exception as e:
            self.logger.error(f"Task planning failed: {e}", extra_data={
                "task_id": task_id,
                "error_type": type(e).__name__
            })
            
            # 记录规划失败的日志
            self.logger.log_agent_action(
                agent_name=self.name,
                action="create_plan",
                details={
                    "task_id": task_id,
                    "success": False,
                    "error": str(e)
                }
            )
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "任务规划失败，请检查任务描述或稍后重试"
            }

    async def _optimize_plan(self, plan: TaskPlan) -> TaskPlan:
        """
        优化生成的计划（可选功能）
        
        Args:
            plan: 原始计划
            
        Returns:
            优化后的计划
        """
        try:
            self.logger.info("Starting plan optimization", extra_data={
                "plan_id": plan.plan_id,
                "original_steps": len(plan.steps)
            })
            
            # 这里可以实现各种优化策略：
            # 1. 合并可以并行执行的步骤
            # 2. 优化工具选择
            # 3. 减少不必要的依赖关系
            # 4. 重新排序步骤以提高效率
            
            # 目前返回原计划，未来可以添加具体的优化逻辑
            optimized_plan = plan
            
            self.logger.info("Plan optimization completed", extra_data={
                "plan_id": plan.plan_id,
                "optimized_steps": len(optimized_plan.steps)
            })
            
            return optimized_plan
            
        except Exception as e:
            self.logger.warning(f"Plan optimization failed, using original plan: {e}")
            return plan

    async def validate_plan(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证计划的有效性
        
        Args:
            plan_data: 计划数据字典
            
        Returns:
            验证结果
        """
        try:
            # 尝试创建TaskPlan对象来验证结构
            plan = TaskPlan(**plan_data)
            
            # 进行额外的逻辑验证
            self.planner._validate_dependencies(plan.steps)
            self.planner._check_circular_dependencies(plan.steps)
            
            return {
                "valid": True,
                "plan_id": plan.plan_id,
                "steps_count": len(plan.steps),
                "message": "计划验证通过"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "message": "计划验证失败"
            }
