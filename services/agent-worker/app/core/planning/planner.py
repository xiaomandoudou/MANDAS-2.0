# services/agent-worker/app/core/planning/planner.py

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.logging.enhanced_logger import EnhancedLogger


# 1. 定义标准化的Plan数据结构 (Pydantic模型)
class PlanStep(BaseModel):
    """任务计划中的单个步骤"""
    step_id: int
    name: str
    description: str
    tool_name: str
    tool_parameters: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[int] = Field(default_factory=list)
    status: str = "QUEUED"  # QUEUED, RUNNING, COMPLETED, FAILED
    result: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None


class TaskPlan(BaseModel):
    """完整的任务执行计划"""
    plan_id: str
    task_id: str
    steps: List[PlanStep]
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "CREATED"  # CREATED, EXECUTING, COMPLETED, FAILED
    total_steps: int = 0
    completed_steps: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        self.total_steps = len(self.steps)


# 2. Prompt模板定义
PLANNING_PROMPT_TEMPLATE = """
# 角色
你是一个顶级的AI任务规划专家。你的唯一职责是根据用户的请求和可用的工具，将一个复杂任务分解为一个由多个步骤组成的、逻辑严密的JSON执行计划。

# 上下文
## 1. 用户任务
{user_prompt}

## 2. 可用工具列表 (JSON格式)
{tools_json}

# 指令
1. **思考**: 请一步一步地思考如何使用上述工具完成用户的任务。
2. **依赖关系**: 仔细分析步骤之间的依赖关系。如果一个步骤的输入依赖于另一个步骤的输出，必须正确设置`dependencies`字段。
3. **参数引用**: 如果一个工具的参数需要使用之前步骤的执行结果，请使用特殊的引用语法 `@{{steps.STEP_ID.result}}`。例如，`"input_text": "@{{steps.1.result}}"`。
4. **输出格式**: 你必须严格按照下面定义的Pydantic JSON Schema格式输出一个JSON对象，不要包含任何额外的解释或Markdown标记。

## 4. 输出的JSON Schema定义
{plan_schema_json}

# 重要提示
- 步骤ID必须从1开始递增
- 依赖关系中的step_id必须小于当前步骤的step_id
- 每个步骤必须有清晰的名称和描述
- 工具参数必须符合工具的要求

# 最终的JSON执行计划:
"""


# 3. TaskPlanner 实现
class TaskPlanner:
    """任务规划器，负责分解和规划复杂任务"""

    def __init__(self, llm_client: Any):
        self.llm_client = llm_client
        self.logger = EnhancedLogger("TaskPlanner")
        self.prompt_template = PLANNING_PROMPT_TEMPLATE

    def _generate_planning_prompt(self, task_description: str, available_tools: List[Dict]) -> str:
        """构建用于生成计划的完整Prompt"""
        try:
            # 简化工具信息，只保留规划需要的关键信息
            simplified_tools = []
            for tool in available_tools:
                simplified_tool = {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "category": tool.get("category", ""),
                    "parameters": tool.get("parameters", {})
                }
                simplified_tools.append(simplified_tool)

            tools_json = json.dumps(simplified_tools, indent=2, ensure_ascii=False)
            
            # 生成TaskPlan的JSON Schema
            plan_schema = {
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "step_id": {"type": "integer"},
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "tool_name": {"type": "string"},
                                "tool_parameters": {"type": "object"},
                                "dependencies": {
                                    "type": "array",
                                    "items": {"type": "integer"}
                                }
                            },
                            "required": ["step_id", "name", "description", "tool_name"]
                        }
                    }
                },
                "required": ["steps"]
            }
            
            plan_schema_json = json.dumps(plan_schema, indent=2, ensure_ascii=False)
            
            prompt = self.prompt_template.format(
                user_prompt=task_description,
                tools_json=tools_json,
                plan_schema_json=plan_schema_json
            )
            
            self.logger.debug("Generated planning prompt", extra_data={
                "prompt_length": len(prompt),
                "tools_count": len(simplified_tools)
            })
            
            return prompt

        except Exception as e:
            self.logger.error(f"Failed to generate planning prompt: {e}")
            raise

    def _validate_dependencies(self, steps: List[PlanStep]) -> bool:
        """验证步骤间的依赖关系"""
        step_ids = {step.step_id for step in steps}
        
        for step in steps:
            # 检查依赖的步骤是否存在
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    raise ValueError(f"步骤 {step.step_id} 的依赖 {dep_id} 不存在")
                
                # 检查依赖的步骤ID是否小于当前步骤ID（防止未来引用）
                if dep_id >= step.step_id:
                    raise ValueError(f"步骤 {step.step_id} 不能依赖未来的步骤 {dep_id}")
        
        return True

    def _check_circular_dependencies(self, steps: List[PlanStep]) -> bool:
        """检查循环依赖"""
        # 构建依赖图
        graph = {step.step_id: step.dependencies for step in steps}
        
        # 使用DFS检测循环
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for step_id in graph:
            if step_id not in visited:
                if has_cycle(step_id):
                    raise ValueError(f"检测到循环依赖，涉及步骤 {step_id}")
        
        return True

    def _parse_plan(self, llm_response: str, task_id: str) -> TaskPlan:
        """解析、验证并返回一个健壮的TaskPlan对象"""
        try:
            # 清理LLM响应，移除可能的Markdown标记
            cleaned_response = llm_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # 解析JSON
            plan_dict = json.loads(cleaned_response)
            
            # 验证基本结构
            if "steps" not in plan_dict:
                raise ValueError("计划中缺少 'steps' 字段")
            
            if not isinstance(plan_dict["steps"], list):
                raise ValueError("'steps' 必须是一个数组")
            
            if len(plan_dict["steps"]) == 0:
                raise ValueError("计划中至少需要一个步骤")
            
            # 创建PlanStep对象
            steps = []
            for step_data in plan_dict["steps"]:
                step = PlanStep(**step_data)
                steps.append(step)
            
            # 验证依赖关系
            self._validate_dependencies(steps)
            self._check_circular_dependencies(steps)
            
            # 创建TaskPlan对象
            plan = TaskPlan(
                plan_id=f"plan-{uuid.uuid4().hex[:8]}",
                task_id=task_id,
                steps=steps
            )
            
            self.logger.info("Successfully parsed and validated task plan", extra_data={
                "plan_id": plan.plan_id,
                "task_id": task_id,
                "steps_count": len(steps)
            })
            
            return plan

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {e}", extra_data={"response": llm_response[:500]})
            raise ValueError(f"LLM返回的不是有效的JSON格式: {e}")
        
        except Exception as e:
            self.logger.error(f"计划解析失败: {e}")
            raise

    async def create_plan(self, task_description: str, task_id: str, available_tools: List[Dict] = None) -> TaskPlan:
        """创建任务执行计划的完整流程"""
        try:
            with self.logger.trace_context(task_id=task_id) as trace_id:
                self.logger.info("Starting task planning", extra_data={
                    "task_description": task_description[:100] + "..." if len(task_description) > 100 else task_description
                })
                
                # 获取可用工具列表
                if available_tools is None:
                    from app.core.tools.tool_registry import ToolRegistry
                    tool_registry = ToolRegistry()
                    await tool_registry.initialize()
                    available_tools = [tool.to_dict() for tool in tool_registry.list_tools()]
                
                # 生成规划Prompt
                prompt = self._generate_planning_prompt(task_description, available_tools)
                
                # 调用LLM生成计划
                self.logger.info("Calling LLM for plan generation")
                llm_response = await self.llm_client.generate(prompt)
                
                # 解析并验证计划
                plan = self._parse_plan(llm_response, task_id)
                
                self.logger.info("Task planning completed successfully", extra_data={
                    "plan_id": plan.plan_id,
                    "steps_count": len(plan.steps)
                })
                
                return plan

        except Exception as e:
            self.logger.error(f"Task planning failed: {e}", extra_data={
                "task_id": task_id,
                "error_type": type(e).__name__
            })
            raise
