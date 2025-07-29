# LLMRouterAgent 模块

## 概述
LLMRouterAgent 是 MANDAS V0.6 的智能路由模块，使用轻量级 LLM 进行模型选择和任务路由决策。

## 功能特性
- 基于 LLM 的智能路由决策
- 模型元数据管理
- 多种路由策略支持
- 决策结果验证和降级处理
- 可扩展的路由算法

## 路由策略
- `llm_based`: 基于 LLM 的智能路由
- `keyword_rules`: 关键词规则路由
- `embedding_similarity`: 嵌入相似度路由
- `load_balancing`: 负载均衡路由

## 使用方法
```python
from app.agents.router.llm_router_agent import LLMRouterAgent
from app.llm.llm_router import LLMRouter

llm_router = LLMRouter()
router_agent = LLMRouterAgent(llm_router)
await router_agent.initialize()

decision = await router_agent.decide(
    "用户查询",
    ["tool1", "tool2"],
    {"priority": 5, "timeout": 300}
)
```

## 决策格式
```json
{
    "model": "选择的模型名称",
    "tools": ["需要的工具列表"],
    "memory_required": true,
    "reasoning": "选择理由",
    "complexity": "medium",
    "estimated_time": "120"
}
```
