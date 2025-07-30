import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from app.llm.llm_router import LLMRouter


class SmartLLMClient:
    """Smart LLM Client for intelligent task planning and execution"""
    
    def __init__(self):
        self.providers = ["openai", "anthropic", "local"]
        self.current_provider = "openai"
        self.llm_router = None
        self.logger = logger.bind(component="SmartLLMClient")
        
    async def initialize(self):
        """Initialize the LLM router"""
        try:
            self.llm_router = LLMRouter()
            await self.llm_router.initialize()
            self.logger.info("SmartLLMClient initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize LLM router: {e}")
            self.llm_router = None
    
    async def generate_plan(self, prompt: str, config: dict = None) -> dict:
        """Generate intelligent task plan"""
        try:
            if not config:
                config = {}
            
            plan_data = await self._create_intelligent_plan(prompt, config)
            
            self.logger.info(f"Generated plan with {len(plan_data.get('steps', []))} steps")
            return plan_data
            
        except Exception as e:
            self.logger.error(f"Error generating plan: {e}")
            return self._create_fallback_plan(prompt)
    
    async def _create_intelligent_plan(self, prompt: str, config: dict) -> dict:
        """Create intelligent plan using LLM analysis"""
        
        task_analysis = await self._analyze_task_complexity(prompt)
        
        steps = await self._generate_plan_steps(prompt, task_analysis, config)
        
        plan_id = str(uuid.uuid4())
        
        return {
            "plan_id": plan_id,
            "task_id": config.get("task_id", "unknown"),
            "summary": f"智能分析任务并生成{len(steps)}个执行步骤的结构化计划",
            "version": "v1.3",
            "steps": steps,
            "created_at": datetime.utcnow().isoformat(),
            "analysis": task_analysis
        }
    
    async def _analyze_task_complexity(self, prompt: str) -> dict:
        """Analyze task complexity and requirements"""
        
        complexity_indicators = {
            "file_operations": any(keyword in prompt.lower() for keyword in ["文件", "读取", "写入", "保存"]),
            "code_analysis": any(keyword in prompt.lower() for keyword in ["代码", "分析", "项目", "程序"]),
            "data_processing": any(keyword in prompt.lower() for keyword in ["数据", "处理", "分析", "统计"]),
            "documentation": any(keyword in prompt.lower() for keyword in ["文档", "说明", "报告", "总结"]),
            "testing": any(keyword in prompt.lower() for keyword in ["测试", "验证", "检查"])
        }
        
        complexity_score = sum(complexity_indicators.values())
        
        return {
            "complexity_score": complexity_score,
            "indicators": complexity_indicators,
            "estimated_steps": min(max(complexity_score * 2, 2), 8),
            "requires_tools": complexity_score > 0
        }
    
    async def _generate_plan_steps(self, prompt: str, analysis: dict, config: dict) -> List[dict]:
        """Generate structured plan steps"""
        
        steps = []
        step_id = 1
        
        steps.append({
            "step_id": step_id,
            "name": "任务分析",
            "description": "分析任务需求和执行策略",
            "tool_name": "task_analyzer",
            "tool_parameters": {"prompt": prompt, "analysis": analysis},
            "dependencies": [],
            "status": "QUEUED"
        })
        step_id += 1
        
        if analysis["indicators"]["file_operations"]:
            steps.append({
                "step_id": step_id,
                "name": "文件操作",
                "description": "执行文件读取、写入或处理操作",
                "tool_name": "file_reader",
                "tool_parameters": {"operation": "read_write"},
                "dependencies": [step_id - 1],
                "status": "QUEUED"
            })
            step_id += 1
        
        if analysis["indicators"]["code_analysis"]:
            steps.append({
                "step_id": step_id,
                "name": "代码分析",
                "description": "分析代码结构和功能",
                "tool_name": "code_analyzer",
                "tool_parameters": {"analysis_type": "structure"},
                "dependencies": [step_id - 1],
                "status": "QUEUED"
            })
            step_id += 1
        
        if analysis["indicators"]["documentation"]:
            steps.append({
                "step_id": step_id,
                "name": "文档生成",
                "description": "生成相关文档和说明",
                "tool_name": "document_generator",
                "tool_parameters": {"format": "markdown"},
                "dependencies": [step_id - 1],
                "status": "QUEUED"
            })
            step_id += 1
        
        if analysis["indicators"]["testing"]:
            steps.append({
                "step_id": step_id,
                "name": "测试验证",
                "description": "创建和执行测试用例",
                "tool_name": "test_runner",
                "tool_parameters": {"test_type": "unit"},
                "dependencies": [step_id - 1],
                "status": "QUEUED"
            })
            step_id += 1
        
        steps.append({
            "step_id": step_id,
            "name": "结果总结",
            "description": "汇总执行结果和输出",
            "tool_name": "result_summarizer",
            "tool_parameters": {"format": "detailed"},
            "dependencies": [step_id - 1],
            "status": "QUEUED"
        })
        
        return steps
    
    def _create_fallback_plan(self, prompt: str) -> dict:
        """Create fallback plan when LLM is unavailable"""
        
        plan_id = str(uuid.uuid4())
        
        return {
            "plan_id": plan_id,
            "task_id": "fallback",
            "summary": "使用默认策略生成的基础执行计划",
            "version": "v1.3-fallback",
            "steps": [
                {
                    "step_id": 1,
                    "name": "任务执行",
                    "description": "执行用户请求的任务",
                    "tool_name": "general_executor",
                    "tool_parameters": {"prompt": prompt},
                    "dependencies": [],
                    "status": "QUEUED"
                },
                {
                    "step_id": 2,
                    "name": "结果输出",
                    "description": "输出执行结果",
                    "tool_name": "result_formatter",
                    "tool_parameters": {"format": "text"},
                    "dependencies": [1],
                    "status": "QUEUED"
                }
            ],
            "created_at": datetime.utcnow().isoformat(),
            "fallback": True
        }
    
    async def chat_completion(self, messages: List[dict], **kwargs) -> dict:
        """Chat completion interface for compatibility"""
        try:
            if self.llm_router:
                return await self.llm_router.chat_completion(messages, **kwargs)
            else:
                return {
                    "choices": [{
                        "message": {
                            "content": "LLM router not available, using fallback response."
                        }
                    }]
                }
        except Exception as e:
            self.logger.error(f"Error in chat completion: {e}")
            return {
                "choices": [{
                    "message": {
                        "content": f"Error: {str(e)}"
                    }
                }]
            }
