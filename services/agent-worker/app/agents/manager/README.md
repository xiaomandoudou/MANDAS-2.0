# GroupChatManager 模块

## 概述
MandasGroupChatManager 是 MANDAS V0.6 的多智能体协同模块，基于 AutoGen 框架实现智能体间的协作。

## 功能特性
- 多智能体协同工作流
- PlannerAgent：任务规划和分解
- EnhancedUserProxyAgent：代码执行和工具调用
- ReviewerAgent：质量审查和结果验证
- 智能对话管理和终止条件

## 智能体角色
- **PlannerAgent**: 负责任务分析、规划制定和步骤分解
- **EnhancedUserProxyAgent**: 负责代码执行、工具调用和实际操作
- **ReviewerAgent**: 负责结果审查、质量验证和改进建议

## 使用方法
```python
from app.agents.manager.group_chat_manager import MandasGroupChatManager

manager = MandasGroupChatManager(tool_registry, execution_guard, memory_manager)
result = await manager.process_task("task_id", "用户需求", config)
```

## 工作流程
1. 任务接收和上下文获取
2. 智能体初始化和配置
3. 多轮对话协作
4. 结果分析和质量检查
5. 最终结果输出和记忆存储
