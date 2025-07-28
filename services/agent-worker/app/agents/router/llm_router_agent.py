import json
import httpx
from typing import Dict, Any, List, Optional
from loguru import logger

from app.core.config import settings
from app.llm.llm_router import LLMRouter


class LLMRouterAgent:
    
    def __init__(self, llm_router: LLMRouter):
        self.llm_router = llm_router
        self.routing_model = "llama3:8b"  # 轻量级模型用于路由决策
        self.model_metadata = {}
        self.model_metadata_file = "/app/configs/model_metadata.yaml"
    
    async def initialize(self):
        await self.llm_router.initialize()
        
        available_models = self.llm_router.available_models
        self.model_metadata = {
            model: self.model_metadata.get(model, {
                "capabilities": ["general"],
                "response_time": "medium",
                "token_cost": "medium",
                "max_context": 4096
            })
            for model in available_models
        }
        
        logger.info("LLM Router Agent initialized successfully")
    
    async def decide(self, user_query: str, available_tools: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            decision_prompt = self._build_decision_prompt(user_query, available_tools, context)
            
            response = await self.llm_router.generate_completion(
                prompt=decision_prompt,
                model=self.routing_model,
                max_tokens=512,
                temperature=0.1  # 低温度确保一致性
            )
            
            decision = self._parse_decision(response)
            
            validated_decision = self._validate_decision(decision, available_tools)
            
            logger.info(f"Routing decision: {validated_decision}")
            return validated_decision
            
        except Exception as e:
            logger.error(f"Error in routing decision: {e}")
            return self._get_fallback_decision(available_tools)
    
    def _build_decision_prompt(self, user_query: str, available_tools: List[str], context: Dict[str, Any] = None) -> str:
        tools_info = "\n".join([f"- {tool}" for tool in available_tools[:10]])
        
        models_info = "\n".join([
            f"- {model}: {meta['capabilities']}, 响应速度: {meta['response_time']}, 成本: {meta['token_cost']}"
            for model, meta in self.model_metadata.items()
        ])
        
        context_info = ""
        if context:
            priority = context.get("priority", 5)
            timeout = context.get("timeout", 300)
            context_info = f"\n任务优先级: {priority}/10\n超时限制: {timeout}秒"
        
        prompt = f"""你是一个智能路由决策器。根据用户查询选择最适合的模型、工具和是否需要记忆。

用户查询: {user_query}

可用模型:
{models_info}

可用工具:
{tools_info}

{context_info}

请分析查询并返回JSON格式的决策:
{{
    "model": "选择的模型名称",
    "tools": ["需要的工具列表"],
    "memory_required": true/false,
    "reasoning": "选择理由",
    "complexity": "low/medium/high",
    "estimated_time": "预估执行时间(秒)"
}}

决策原则:
1. 编程任务选择code模型 (如codellama, qwen3)
2. 复杂分析选择大模型 (如qwen3:72b)
3. 简单对话选择轻量模型 (如llama3:8b)
4. 需要执行代码时包含相关工具
5. 涉及历史信息时启用记忆

请返回JSON格式决策:
{{
    "model": "选择的模型名称",
    "tools": ["需要的工具列表"],
    "memory_required": true/false,
    "reasoning": "选择理由",
    "complexity": "low/medium/high",
    "estimated_time": "预估执行时间(秒)"
}}

JSON决策:"""
        
        return prompt
    
    def _parse_decision(self, response: str) -> Dict[str, Any]:
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[start_idx:end_idx]
            decision = json.loads(json_str)
            
            required_fields = ["model", "tools", "memory_required"]
            for field in required_fields:
                if field not in decision:
                    decision[field] = self._get_default_value(field)
            
            return decision
            
        except Exception as e:
            logger.error(f"Error parsing decision response: {e}")
            return self._get_fallback_decision([])
    
    def _validate_decision(self, decision: Dict[str, Any], available_tools: List[str]) -> Dict[str, Any]:
        if decision["model"] not in self.model_metadata:
            decision["model"] = list(self.model_metadata.keys())[0]
        
        valid_tools = [tool for tool in decision.get("tools", []) if tool in available_tools]
        decision["tools"] = valid_tools
        
        decision["memory_required"] = bool(decision.get("memory_required", False))
        
        decision["routing_strategy"] = "llm_based"
        decision["router_model"] = self.routing_model
        
        return decision
    
    def _get_default_value(self, field: str) -> Any:
        defaults = {
            "model": list(self.model_metadata.keys())[0] if self.model_metadata else "llama3:8b",
            "tools": [],
            "memory_required": False,
            "reasoning": "Default routing decision",
            "complexity": "medium",
            "estimated_time": "60"
        }
        return defaults.get(field, None)
    
    def _get_fallback_decision(self, available_tools: List[str]) -> Dict[str, Any]:
        return {
            "model": list(self.model_metadata.keys())[0] if self.model_metadata else "llama3:8b",
            "tools": available_tools[:3] if available_tools else [],
            "memory_required": True,
            "reasoning": "Fallback decision due to parsing error",
            "complexity": "medium",
            "estimated_time": "120",
            "routing_strategy": "fallback",
            "router_model": self.routing_model
        }
    
    async def get_routing_strategies(self) -> List[str]:
        return [
            "llm_based",      # 基于LLM的智能路由
            "keyword_rules",  # 关键词规则路由
            "embedding_similarity",  # 嵌入相似度路由
            "load_balancing"  # 负载均衡路由
        ]
    
    async def update_model_metadata(self, model: str, metadata: Dict[str, Any]):
        if model in self.model_metadata:
            self.model_metadata[model].update(metadata)
            logger.info(f"Updated metadata for model {model}")
