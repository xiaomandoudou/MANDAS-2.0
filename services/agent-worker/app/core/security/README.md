# ExecutionGuard 模块

## 概述
ExecutionGuard 是 MANDAS V0.6 的安全执行模块，提供 Docker 沙箱隔离和权限管理功能。

## 功能特性
- Docker 容器沙箱隔离
- 资源限制（CPU、内存、网络）
- 自动容器清理
- 权限检查和安全策略
- 危险命令检测

## 使用方法
```python
from app.core.security.execution_guard import ExecutionGuard
from app.core.tools.tool_registry import ToolRegistry

tool_registry = ToolRegistry()
execution_guard = ExecutionGuard(tool_registry)
await execution_guard.initialize()

result = await execution_guard.execute_tool(
    "python_executor",
    {"code": "print('Hello World')"},
    {"task_id": "test", "user_id": "user123"}
)
```

## 安全策略
- 阻止危险命令：`rm -rf`, `sudo`, `su`
- 容器资源限制：默认 512MB 内存，0.5 CPU
- 网络隔离：默认禁用网络访问
- 执行超时：默认 300 秒
