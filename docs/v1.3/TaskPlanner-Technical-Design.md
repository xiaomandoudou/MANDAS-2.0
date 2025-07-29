# MANDAS V1.3 - TaskPlanner 模块技术设计文档

## 1. 概述

TaskPlanner 是MANDAS V1.3版本引入的核心智能模块。它作为系统的"思考者"，负责将用户输入的、模糊的自然语言任务，转化为一个结构化的、机器可读的、包含依赖关系的执行计划（Plan）。本文档详细阐述其内部实现机制。

## 2. 核心职责与方法

### 2.1 主要方法

- **`create_plan(task_description, available_tools)`**: 接收任务描述和可用工具列表，调用LLM生成一个结构化的TaskPlan对象。
- **`_generate_planning_prompt(...)`**: 内部方法，负责构建高质量的Prompt，这是确保规划成功的关键。
- **`_parse_plan(...)`**: 内部方法，负责解析和验证LLM返回的JSON，确保计划的健壮性和安全性。

### 2.2 设计原则

1. **结构化输出**: 将自然语言转换为机器可读的JSON格式
2. **依赖关系管理**: 正确处理步骤间的依赖关系
3. **健壮性验证**: 多层验证确保计划的可执行性
4. **工具集成**: 与现有ToolRegistry无缝集成

## 3. Prompt工程 (_generate_planning_prompt) 深度解析

为了引导LLM稳定地输出我们需要的结构化JSON，我们将采用一个包含角色设定、上下文、严格指令和输出格式定义的复杂Prompt模板。

### 3.1 Prompt 模板结构

```python
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

# 最终的JSON执行计划:
"""
```

### 3.2 模板详解

- **角色**: 赋予LLM一个专家身份，有助于提高其输出的专业性
- **上下文**:
  - `{user_prompt}`: 用户的原始指令
  - `{tools_json}`: 将ToolRegistry中所有工具的元数据序列化为JSON字符串
- **指令**: 通过明确的指令约束LLM的行为，强调思考、依赖关系、参数引用和严格的输出格式
- **输出的JSON Schema定义**: 将TaskPlan的Pydantic模型转换为JSON Schema字符串

## 4. 计划解析与验证 (_parse_plan) 深度解析

LLM的输出本质上是不可靠的，因此必须有一个强大的解析和验证层。

### 4.1 验证层次

1. **JSON解析**: 尝试用`json.loads()`解析LLM返回的字符串
2. **Pydantic验证**: 将解析后的字典传入TaskPlan的Pydantic模型进行验证
3. **逻辑验证**:
   - **依赖关系检查**: 确保dependencies中引用的step_id是真实存在的
   - **循环依赖检查**: 构建有向图，检查计划中是否存在循环依赖
   - **工具存在性检查**: 确保每个步骤中引用的tool_name都在ToolRegistry中存在

### 4.2 错误处理策略

- 解析失败时触发重试机制
- 提供详细的错误信息用于调试
- 支持降级策略（简化任务或使用默认计划）

## 5. 数据结构定义

### 5.1 PlanStep 模型

```python
class PlanStep(BaseModel):
    step_id: int
    name: str
    description: str
    tool_name: str
    tool_parameters: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[int] = Field(default_factory=list)
    status: str = "QUEUED"
```

### 5.2 TaskPlan 模型

```python
class TaskPlan(BaseModel):
    plan_id: str
    task_id: str
    steps: List[PlanStep]
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "CREATED"
```

## 6. 架构集成

### 6.1 与现有系统的集成点

- **ToolRegistry**: 获取可用工具列表
- **LLM Router**: 选择合适的LLM进行规划
- **Memory Manager**: 存储和检索规划历史
- **Task Consumer**: 执行生成的计划

### 6.2 数据流

```
用户输入 → TaskPlanner → 结构化计划 → PlannerAgent → GroupChatManager → 执行代理
```

## 7. 性能优化

### 7.1 缓存策略

- 相似任务的计划缓存
- 工具元数据缓存
- Prompt模板缓存

### 7.2 并发处理

- 支持多个任务同时规划
- 异步LLM调用
- 批量验证优化

## 8. 监控与调试

### 8.1 日志记录

- 详细的规划过程日志
- LLM调用追踪
- 验证失败原因记录

### 8.2 指标监控

- 规划成功率
- 平均规划时间
- 计划执行成功率

## 9. 扩展性设计

### 9.1 插件化架构

- 支持自定义验证器
- 可扩展的Prompt模板
- 多种LLM后端支持

### 9.2 未来功能

- 动态计划调整
- 智能重试机制
- 计划优化建议

---

**版本**: V1.3  
**作者**: MANDAS开发团队  
**更新时间**: 2025-07-29
