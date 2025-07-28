# Contributing to MANDAS-2.0

感谢您对 Mandas Modular Agent System 的贡献！

## 开发环境设置

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+
- Node.js 18+
- Poetry (Python 包管理器)

### 快速开始

1. 克隆项目
```bash
git clone https://github.com/xiaomandoudou/MANDAS-2.0.git
cd MANDAS-2.0
```

2. 运行设置脚本
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

3. 启动开发环境
```bash
# 使用 Docker Compose
docker-compose up -d

# 或者分别启动各个服务
make dev-api      # API Gateway
make dev-worker   # Agent Worker
make dev-frontend # Frontend
```

## 项目结构

```
MANDAS-2.0/
├── services/
│   ├── api-gateway/          # API网关服务 (FastAPI)
│   ├── agent-worker/         # Agent工作节点 (Python)
│   └── frontend/            # 前端界面 (React + TypeScript)
├── database/                # 数据库初始化脚本
├── scripts/                 # 开发脚本
├── docker-compose.yml       # 生产环境配置
├── docker-compose.dev.yml   # 开发环境配置
└── Makefile                # 开发命令
```

## 开发工作流

### 1. 创建功能分支

```bash
git checkout -b feature/your-feature-name
```

### 2. 开发和测试

```bash
# 运行测试
make test

# 代码格式化
make format

# 代码检查
make lint
```

### 3. 提交代码

```bash
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

### 4. 创建 Pull Request

在 GitHub 上创建 Pull Request，描述您的更改。

## 代码规范

### Python 代码

- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 使用 flake8 进行代码检查
- 遵循 PEP 8 规范

### TypeScript/React 代码

- 使用 ESLint 进行代码检查
- 使用 Prettier 进行代码格式化
- 遵循 React 最佳实践

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式化
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

## 测试

### 单元测试

```bash
# API Gateway 测试
cd services/api-gateway
poetry run pytest

# Agent Worker 测试
cd services/agent-worker
poetry run pytest

# Frontend 测试
cd services/frontend
npm test
```

### 集成测试

```bash
# 运行所有测试
make test
```

## 文档

- API 文档：启动服务后访问 http://localhost:8080/docs
- 架构文档：查看项目根目录的文档文件
- 代码注释：重要的业务逻辑需要添加注释

## 问题报告

如果您发现 bug 或有功能建议，请：

1. 检查是否已有相关 issue
2. 创建新的 issue，详细描述问题
3. 提供复现步骤和环境信息

## 许可证

本项目采用 AGPL-3.0 许可证。贡献代码即表示您同意将您的贡献以相同许可证发布。

## 联系我们

- GitHub Issues: https://github.com/xiaomandoudou/MANDAS-2.0/issues
- GitHub Discussions: https://github.com/xiaomandoudou/MANDAS-2.0/discussions

感谢您的贡献！🎉
