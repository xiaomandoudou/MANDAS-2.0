# MANDAS V2.0 - API接口规范文档

**版本**: 2.0  
**基础路径**: `/mandas/v2`

## 1. 概述

V2.0引入了一套全新的API，专门用于管理和执行多代理工作流 (Workflows)。原有V1版本的`/tasks`接口将继续保留，用于处理单Agent任务。

## 2. 核心数据模型

### WorkflowDefinition
对应workflows数据库表的模型，包含id, name, definition_yaml等。

```json
{
  "id": "workflow-12345",
  "name": "月度销售报告生成工作流",
  "description": "一个自动化分析销售数据并生成报告的Agent团队",
  "definition_yaml": "...",
  "version": 1,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

### WorkflowRun
对应workflow_runs数据库表的模型，包含id, status, final_output等。

```json
{
  "id": "run-f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "workflow_id": "workflow-12345",
  "status": "COMPLETED",
  "initial_input": {
    "sales_report_url": "http://example.com/sales.pdf"
  },
  "final_output": {
    "report_url": "http://example.com/generated-report.pdf",
    "summary": "销售额同比增长15%"
  },
  "duration_ms": 45000,
  "started_at": "2025-01-01T10:00:00Z",
  "completed_at": "2025-01-01T10:00:45Z"
}
```

## 3. API 端点 (Endpoints)

### 工作流定义管理 (Workflow Definition Management)

#### POST /workflows
**功能**: 创建一个新的工作流定义。

**请求体**: `application/json`
```json
{
  "name": "月度销售报告生成工作流",
  "description": "一个自动化分析销售数据并生成报告的Agent团队。",
  "definition_yaml": "name: 销售报告工作流\ndescription: 自动化销售数据分析\nagents:\n  - name: DataAnalyzer\n    type: data_analysis\n  - name: ReportGenerator\n    type: report_generation"
}
```

**响应 (201 Created)**: 返回创建的WorkflowDefinition对象。

#### GET /workflows
**功能**: 获取所有已保存的工作流定义列表。

**查询参数**:
- `page`: 页码 (默认: 1)
- `limit`: 每页数量 (默认: 20)
- `search`: 搜索关键词

**响应 (200 OK)**: 返回WorkflowDefinition对象列表。

#### GET /workflows/{workflow_id}
**功能**: 获取单个工作流的详细定义。

**响应 (200 OK)**: 返回完整的WorkflowDefinition对象。

#### PUT /workflows/{workflow_id}
**功能**: 更新工作流定义。

**请求体**: `application/json`
```json
{
  "name": "更新后的工作流名称",
  "description": "更新后的描述",
  "definition_yaml": "..."
}
```

#### DELETE /workflows/{workflow_id}
**功能**: 删除工作流定义。

**响应 (204 No Content)**: 成功删除。

### 工作流执行管理 (Workflow Run Management)

#### POST /workflows/{workflow_id}/run
**功能**: 启动一次指定工作流的执行。

**描述**: 这是一个异步接口，会立即返回一个run_id。

**请求体**: `application/json`
```json
{
  "initial_input": {
    "sales_report_url": "http://example.com/sales.pdf",
    "report_format": "pdf",
    "include_charts": true
  }
}
```

**响应 (202 Accepted)**:
```json
{
  "run_id": "run-f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "QUEUED",
  "message": "Workflow run has been queued."
}
```

#### GET /workflows/runs/{run_id}
**功能**: 查询某次工作流执行的状态和结果。

**响应 (200 OK)**: 返回WorkflowRun对象，其中可能包含每个Agent的详细执行日志。

```json
{
  "id": "run-f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "workflow_id": "workflow-12345",
  "status": "RUNNING",
  "progress": {
    "current_step": 2,
    "total_steps": 4,
    "current_agent": "ReportGenerator"
  },
  "agent_results": [
    {
      "agent_name": "DataAnalyzer",
      "status": "COMPLETED",
      "output": {
        "analysis_result": "销售数据分析完成"
      },
      "duration_ms": 15000
    }
  ]
}
```

#### GET /workflows/runs
**功能**: 获取工作流执行历史列表。

**查询参数**:
- `workflow_id`: 过滤特定工作流
- `status`: 过滤执行状态
- `page`: 页码
- `limit`: 每页数量

#### DELETE /workflows/runs/{run_id}
**功能**: 取消正在执行的工作流。

**响应 (200 OK)**:
```json
{
  "message": "Workflow run has been cancelled.",
  "status": "CANCELLED"
}
```

## 4. 状态码和错误处理

### 标准HTTP状态码
- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `202 Accepted`: 请求已接受，异步处理中
- `204 No Content`: 请求成功，无返回内容
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `409 Conflict`: 资源冲突
- `500 Internal Server Error`: 服务器内部错误

### 错误响应格式
```json
{
  "error": {
    "code": "WORKFLOW_NOT_FOUND",
    "message": "指定的工作流不存在",
    "details": {
      "workflow_id": "workflow-12345"
    }
  }
}
```

## 5. 认证和授权

### API密钥认证
```http
Authorization: Bearer your-api-key
```

### 权限级别
- `READ`: 查看工作流定义和执行结果
- `WRITE`: 创建和修改工作流定义
- `EXECUTE`: 执行工作流
- `ADMIN`: 所有权限

## 6. 限流和配额

### 请求限制
- 每分钟最多100个API请求
- 并发工作流执行数限制为10个
- 单个工作流最长执行时间为1小时

### 响应头
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```
