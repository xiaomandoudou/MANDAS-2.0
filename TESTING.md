# MANDAS-2.0 测试指南

本文档介绍如何运行和使用MANDAS-2.0项目的测试套件。

## 🚀 快速开始

### 1. 环境检查

首先运行快速环境检查：

```bash
python quick_test.py
```

这将检查：
- Python版本和依赖包
- 测试文件完整性
- GitHub Actions配置
- Docker可用性
- 基本测试功能

### 2. 安装测试依赖

```bash
pip install -r requirements-dev.txt
```

主要测试依赖：
- `pytest` - 测试框架
- `pytest-cov` - 代码覆盖率
- `requests` - HTTP客户端
- `websocket-client` - WebSocket客户端
- `psycopg-binary` - PostgreSQL数据库适配器

### 3. 运行测试

#### 运行所有测试
```bash
python -m pytest tests/ -v
```

#### 运行特定测试套件
```bash
# API路由测试
python -m pytest tests/test_api_routes.py -v

# 数据库迁移测试
python -m pytest tests/test_database_migration.py -v

# Agent抽象层测试
python -m pytest tests/test_agent_abstractions.py -v

# 端到端测试
python -m pytest tests/test_end_to_end.py -v
```

#### 生成覆盖率报告
```bash
python -m pytest tests/ --cov=. --cov-report=html
```

## 📋 测试套件说明

### 1. API路由测试 (`test_api_routes.py`)
- 测试API端点的基本功能
- 验证请求/响应格式
- 检查错误处理
- 验证新的`/mandas/v1/`路由前缀

### 2. 数据库迁移测试 (`test_database_migration.py`)
- 验证数据库表结构
- 测试`metadata`到`log_metadata`列的重命名
- 检查数据完整性
- 验证外键约束

### 3. Agent抽象层测试 (`test_agent_abstractions.py`)
- 测试V1.2版本的BaseAgent和BaseTool抽象
- 验证DefaultAgent实现
- 测试工具注册表功能
- 检查增强日志系统

### 4. 端到端测试 (`test_end_to_end.py`)
- 完整的任务执行流程测试
- WebSocket实时通信测试
- 多工具协同测试
- 任务状态转换验证

## 🐳 Docker测试环境

### 使用Docker Compose运行测试

```bash
# 启动测试环境
docker-compose -f docker-compose.test.yml up --build

# 仅运行测试服务
docker-compose -f docker-compose.test.yml up test-runner
```

测试环境包括：
- PostgreSQL 15 (端口5433)
- Redis 7 (端口6380)
- 测试运行器容器

### 手动Docker测试

```bash
# 构建测试镜像
docker build -f Dockerfile.test -t mandas-test .

# 运行测试
docker run --rm mandas-test
```

## 🔧 GitHub Actions CI/CD

### 工作流触发条件
- 推送到`main`或`develop`分支
- 创建或更新Pull Request
- 手动触发

### 工作流阶段
1. **代码质量检查** - Black、isort、flake8、mypy
2. **后端测试** - Python单元测试和集成测试
3. **前端测试** - JavaScript/TypeScript测试
4. **集成测试** - 端到端测试
5. **部署检查** - 部署就绪验证

### 检查PR状态

```bash
# 检查PR #1的状态
python check_github_status.py 1

# 等待检查完成
python check_github_status.py 1 --wait

# 使用GitHub Token（可选）
python check_github_status.py 1 --token YOUR_GITHUB_TOKEN
```

## 📊 测试覆盖率

目标覆盖率：
- 单元测试：≥ 80%
- 集成测试：≥ 70%
- 端到端测试：≥ 60%

查看覆盖率报告：
```bash
# 生成HTML报告
python -m pytest tests/ --cov=. --cov-report=html

# 打开报告
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

## 🐛 故障排除

### 常见问题

1. **psycopg导入错误**
   ```bash
   pip install psycopg-binary
   ```

2. **Docker连接失败**
   - 确保Docker服务正在运行
   - 检查端口是否被占用

3. **测试超时**
   - 增加pytest超时设置
   - 检查服务是否正常启动

4. **WebSocket连接失败**
   - 确保应用服务正在运行
   - 检查防火墙设置

### 调试技巧

1. **详细输出**
   ```bash
   python -m pytest tests/ -v -s
   ```

2. **只运行失败的测试**
   ```bash
   python -m pytest tests/ --lf
   ```

3. **进入调试模式**
   ```bash
   python -m pytest tests/ --pdb
   ```

## 📈 持续改进

### 添加新测试

1. 在`tests/`目录下创建新的测试文件
2. 遵循命名约定：`test_*.py`
3. 使用适当的测试标记：`@pytest.mark.unit`、`@pytest.mark.integration`
4. 更新此文档

### 性能测试

```bash
# 运行性能测试
python -m pytest tests/ -m slow --durations=10
```

### 测试数据管理

- 测试数据存放在`tests/fixtures/`
- 数据库初始化脚本在`tests/sql/`
- 使用工厂模式创建测试数据

## 🔗 相关链接

- [pytest文档](https://docs.pytest.org/)
- [GitHub Actions文档](https://docs.github.com/en/actions)
- [Docker Compose文档](https://docs.docker.com/compose/)
- [psycopg文档](https://www.psycopg.org/psycopg3/)

---

如有问题，请提交Issue或联系开发团队。
