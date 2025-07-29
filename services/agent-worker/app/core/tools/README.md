# ToolRegistry 模块

## 概述
ToolRegistry 是 MANDAS V0.6 的工具注册中心，提供工具注册、发现和权限控制功能。

## 功能特性
- 动态工具加载（YAML/JSON 配置）
- OpenAPI Schema 支持
- 权限检查和访问控制
- 工具元数据管理
- 分类和版本管理

## 配置格式
```yaml
name: "tool_name"
description: "工具描述"
category: "utility"
version: "1.0.0"
author: "作者"
enabled: true
timeout: 300
rate_limit_per_min: 60
required_permissions: ["permission1"]
parameters:
  type: "object"
  properties:
    param1:
      type: "string"
      description: "参数描述"
  required: ["param1"]
```

## 使用方法
```python
from app.core.tools.tool_registry import ToolRegistry

registry = ToolRegistry("/app/tools.d")
await registry.initialize()

tools = registry.list_tools()
tool = registry.get_tool("echo")
has_permission = await registry.check_permission("echo", user_context)
```
