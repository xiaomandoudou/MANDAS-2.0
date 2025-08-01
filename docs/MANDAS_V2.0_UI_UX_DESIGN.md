# MANDAS V2.0 - UI/UX 设计说明

## 1. 版本目标

为V2.0的多代理协作框架提供全新的、独立的工作流管理界面，让用户可以直观地创建、管理和监控Agent团队的协作过程。

## 2. 设计原则

### 2.1 用户体验原则
- **简洁直观**: 界面简洁，操作流程清晰
- **实时反馈**: 提供即时的状态更新和进度反馈
- **错误友好**: 清晰的错误提示和恢复建议
- **响应式设计**: 支持桌面和移动设备

### 2.2 视觉设计原则
- **一致性**: 统一的设计语言和交互模式
- **层次清晰**: 合理的信息架构和视觉层次
- **品牌统一**: 与MANDAS品牌形象保持一致

## 3. 新增核心页面

### 3.1 页面: 工作流市场 (Workflow Marketplace)

**路径**: `/workflows`

**布局**: 采用卡片式布局，每个卡片代表一个已保存的工作流。

**功能**:
- **工作流列表**: 展示所有WorkflowDefinition
- **新建工作流**: 右上角提供"新建工作流"按钮，点击后进入"工作流编辑器"页面
- **快速操作**: 每个卡片上提供"运行"、"编辑"、"删除"等快捷操作按钮
- **搜索和过滤**: 支持按名称、标签、创建时间等条件筛选
- **批量操作**: 支持批量删除、导出等操作

**界面元素**:
```
┌─────────────────────────────────────────────────────────────┐
│ MANDAS V2.0 - 工作流市场                    [+ 新建工作流] │
├─────────────────────────────────────────────────────────────┤
│ 🔍 搜索工作流...                    📊 全部 | 🏃 运行中 | ✅ 完成 │
├─────────────────────────────────────────────────────────────┤
│ ┌────────────┐ ┌─────────────┐ ┌─────────────┐           │
│ │ 📊 销售报告  │ │ 📧 邮件营销  │ │ 🔍 数据分析  │           │
│ │ 生成工作流   │ │ 自动化工作流 │ │ 工作流      │           │
│ │             │ │             │ │             │           │
│ │ 最后运行:    │ │ 最后运行:    │ │ 最后运行:    │           │
│ │ 2小时前     │ │ 1天前       │ │ 3天前       │           │
│ │             │ │             │ │             │           │
│ │ [▶️运行][✏️编辑] │ │ [▶️运行][✏️编辑] │ │ [▶️运行][✏️编辑] │           │
│ └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 页面: 工作流编辑器 (Workflow Editor)

**路径**: `/workflows/editor/{workflow_id}`

**布局**: 采用左右分栏布局。

**左侧**: 一个基于react-ace或monaco-editor的YAML编辑器，提供语法高亮和基本的校验功能。

**右侧**: 一个"文档与预览"区域，用于展示工作流YAML规范的说明文档，并可能在未来提供一个简单的可视化预览。

**功能**:
- **编辑与保存**: 用户可以直接在编辑器中编写和修改工作流的YAML定义
- **实时校验**: 提供YAML语法和工作流规范的实时校验
- **模板支持**: 提供常用工作流模板
- **版本管理**: 支持工作流版本历史和回滚
- **运行**: 提供"保存并运行"按钮，用于保存定义并启动一次新的执行

**界面布局**:
```
┌─────────────────────────────────────────────────────────────┐
│ 📝 工作流编辑器 - 销售报告生成工作流        [💾保存] [▶️运行] │
├─────────────────────┬───────────────────────────────────────┤
│ YAML编辑器          │ 文档与预览                            │
│                     │                                       │
│ name: 销售报告工作流 │ 📖 工作流YAML规范                     │
│ description: ...    │                                       │
│ agents:             │ 基本结构:                             │
│   - name: Analyzer  │ - name: 工作流名称                    │
│     type: data      │ - description: 工作流描述             │
│   - name: Generator │ - agents: Agent列表                   │
│     type: report    │   - name: Agent名称                   │
│                     │   - type: Agent类型                   │
│ ✅ YAML语法正确      │                                       │
│ ✅ 工作流规范通过    │ 🔍 可视化预览 (即将推出)              │
│                     │                                       │
│                     │ Agent A → Agent B → Agent C           │
└─────────────────────┴───────────────────────────────────────┘
```

### 3.3 页面: 工作流执行详情 (Workflow Run Detail)

**路径**: `/workflows/runs/{run_id}`

**布局**:
- **顶部**: 显示本次运行的总体信息（ID, 状态, 耗时, 最终结果）
- **主体**: 一个时间线或简化的步骤列表视图，展示工作流中每个Agent的执行情况

**功能**:
- **Agent执行详情**: 每个步骤都可展开，查看该Agent的输入、输出和关键日志摘要
- **实时更新**: （可选，M2阶段后）页面可以通过WebSocket接收实时状态更新
- **错误诊断**: 详细的错误信息和建议解决方案
- **性能分析**: 各个Agent的执行时间和资源使用情况

**界面布局**:
```
┌─────────────────────────────────────────────────────────────┐
│ 🏃 工作流执行详情 - run-f47ac10b                    [🔄刷新] │
├─────────────────────────────────────────────────────────────┤
│ 状态: ✅ 已完成  |  耗时: 45秒  |  开始时间: 10:00:00       │
│ 工作流: 销售报告生成工作流                                  │
├─────────────────────────────────────────────────────────────┤
│ 📊 执行进度                                                 │
│                                                             │
│ ✅ DataAnalyzer     (15秒)  ──→  ✅ ReportGenerator (20秒) │
│    │ 输入: sales_data.csv        │ 输入: analysis_result   │
│    │ 输出: analysis_result       │ 输出: final_report.pdf  │
│    └─ 📋 查看详细日志            └─ 📋 查看详细日志        │
│                                                             │
│ 🎯 最终输出:                                                │
│ {                                                           │
│   "report_url": "http://example.com/report.pdf",           │
│   "summary": "销售额同比增长15%"                            │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

## 4. 交互设计

### 4.1 状态指示
- **工作流状态**: 使用颜色和图标清晰表示状态
  - 🟢 运行中 (绿色)
  - ✅ 已完成 (蓝色)
  - ❌ 失败 (红色)
  - ⏸️ 暂停 (黄色)

### 4.2 操作反馈
- **加载状态**: 使用骨架屏和进度条
- **操作确认**: 重要操作需要二次确认
- **成功提示**: 使用Toast消息提示操作结果

### 4.3 响应式设计
- **桌面端**: 充分利用屏幕空间，支持多窗口操作
- **移动端**: 优化触摸操作，简化界面层次

## 5. 技术实现

### 5.1 前端技术栈
- **框架**: React 18 + TypeScript
- **状态管理**: Zustand 或 Redux Toolkit
- **UI组件**: Ant Design 或 Chakra UI
- **代码编辑器**: Monaco Editor
- **图表**: D3.js 或 Recharts

### 5.2 实时通信
- **WebSocket**: 用于实时状态更新
- **Server-Sent Events**: 备选方案
- **轮询**: 降级方案

## 6. 可访问性

### 6.1 键盘导航
- 支持Tab键导航
- 快捷键支持
- 焦点管理

### 6.2 屏幕阅读器
- 语义化HTML
- ARIA标签
- 替代文本

## 7. 性能优化

### 7.1 加载优化
- 代码分剂
- 懒加载
- 缓存策略

### 7.2 渲染优化
- 虚拟滚动
- 防抖和节流
- 组件优化
