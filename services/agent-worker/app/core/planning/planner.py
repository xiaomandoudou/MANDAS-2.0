from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from loguru import logger
import json
import uuid
from datetime import datetime

from app.llm.llm_router import LLMRouter


@dataclass
class PlanStep:
    """Individual step in a task plan"""
    step_id: int
    name: str
    description: str
    tool_name: str
    tool_parameters: Dict[str, Any]
    dependencies: List[int]
    status: str = "QUEUED"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    result_preview: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert PlanStep to dictionary"""
        return asdict(self)


@dataclass
class TaskPlan:
    """Complete task execution plan"""
    plan_id: str
    task_id: str
    summary: str
    version: str
    steps: List[PlanStep]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert TaskPlan to dictionary"""
        return {
            "plan_id": self.plan_id,
            "task_id": self.task_id,
            "summary": self.summary,
            "version": self.version,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at
        }


class TaskPlanner:
    """Intelligent task planning engine that converts natural language tasks into structured execution plans"""
    
    def __init__(self, llm_router: LLMRouter):
        self.llm_router = llm_router
        self.logger = logger.bind(component="TaskPlanner")
    
    async def create_plan(self, task_description: str, available_tools: List[str], task_id: str) -> TaskPlan:
        """
        Create a structured execution plan for a given task
        
        Args:
            task_description: Natural language description of the task
            available_tools: List of available tool names
            task_id: Unique identifier for the task
            
        Returns:
            TaskPlan object with structured steps and dependencies
        """
        self.logger.info(f"Creating plan for task: {task_id}")
        
        try:
            planning_prompt = self._generate_planning_prompt(task_description, available_tools)
            
            llm_response = await self.llm_router.chat_completion(
                messages=[{"role": "user", "content": planning_prompt}],
                temperature=0.1
            )
            
            plan_data = self._parse_plan(llm_response, task_id)
            
            self.logger.info(f"Successfully created plan with {len(plan_data.steps)} steps")
            return plan_data
            
        except Exception as e:
            self.logger.error(f"Failed to create plan for task {task_id}: {str(e)}")
            return TaskPlan(
                plan_id=str(uuid.uuid4()),
                task_id=task_id,
                summary="任务无需规划，直接进入执行阶段。",
                version="v1",
                steps=[],
                created_at=datetime.utcnow().isoformat()
            )
    
    def _generate_planning_prompt(self, task_description: str, available_tools: List[str]) -> str:
        """Generate a high-quality prompt for LLM to create structured plans"""
        
        tools_description = "\n".join([f"- {tool}" for tool in available_tools])
        
        prompt = f"""
你是一个智能任务规划专家。请将以下自然语言任务分解为结构化的执行步骤。

任务描述：
{task_description}

可用工具：
{tools_description}

请返回一个JSON格式的执行计划，包含以下结构：
{{
  "summary": "对整个计划的简要描述",
  "steps": [
    {{
      "step_id": 1,
      "name": "步骤名称",
      "description": "详细描述这个步骤要做什么",
      "tool_name": "使用的工具名称",
      "tool_parameters": {{"参数名": "参数值"}},
      "dependencies": [前置步骤的step_id列表]
    }}
  ]
}}

规划原则：
1. 步骤要逻辑清晰，有明确的依赖关系
2. 每个步骤只使用一个工具
3. 参数中可以使用 "@{{steps.N.result}}" 引用前面步骤的结果
4. 如果任务很简单，可以只有1-2个步骤
5. 如果任务不需要工具，返回空的steps数组

请只返回JSON，不要包含其他文字。
"""
        return prompt
    
    def _parse_plan(self, llm_response: str, task_id: str) -> TaskPlan:
        """Parse LLM response into structured TaskPlan object"""
        
        try:
            content = llm_response.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            plan_json = json.loads(content.strip())
            
            steps = []
            for step_data in plan_json.get("steps", []):
                step = PlanStep(
                    step_id=step_data["step_id"],
                    name=step_data["name"],
                    description=step_data["description"],
                    tool_name=step_data["tool_name"],
                    tool_parameters=step_data["tool_parameters"],
                    dependencies=step_data.get("dependencies", [])
                )
                steps.append(step)
            
            plan = TaskPlan(
                plan_id=str(uuid.uuid4()),
                task_id=task_id,
                summary=plan_json.get("summary", "执行计划已生成"),
                version="v1",
                steps=steps,
                created_at=datetime.utcnow().isoformat()
            )
            
            return plan
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self.logger.error(f"Failed to parse plan from LLM response: {str(e)}")
            
            return TaskPlan(
                plan_id=str(uuid.uuid4()),
                task_id=task_id,
                summary="规划解析失败，将使用默认执行流程",
                version="v1",
                steps=[],
                created_at=datetime.utcnow().isoformat()
            )
    
    async def regenerate_plan(self, task_id: str, task_description: str, available_tools: List[str], current_version: str = "v1") -> TaskPlan:
        """Regenerate a plan with a new version"""
        
        self.logger.info(f"Regenerating plan for task: {task_id}")
        
        new_plan = await self.create_plan(task_description, available_tools, task_id)
        
        version_num = int(current_version.replace("v", "")) + 1
        new_plan.version = f"v{version_num}"
        
        return new_plan
