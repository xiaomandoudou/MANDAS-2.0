-- 测试数据库初始化脚本
-- 创建MANDAS系统所需的基本表结构

-- 启用UUID扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建任务表
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'QUEUED' CHECK (status IN ('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'RETRYING')),
    prompt TEXT NOT NULL,
    plan JSONB,
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    retry_count INTEGER DEFAULT 0
);

-- 创建日志表
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    level VARCHAR(20) DEFAULT 'INFO' CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    log_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建工具注册表
CREATE TABLE IF NOT EXISTS tools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    config JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建用户表（如果需要）
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);

CREATE INDEX IF NOT EXISTS idx_logs_task_id ON logs(task_id);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);

CREATE INDEX IF NOT EXISTS idx_tools_name ON tools(name);
CREATE INDEX IF NOT EXISTS idx_tools_is_active ON tools(is_active);

-- 创建更新时间戳的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为tasks表创建更新时间戳触发器
DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks;
CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为tools表创建更新时间戳触发器
DROP TRIGGER IF EXISTS update_tools_updated_at ON tools;
CREATE TRIGGER update_tools_updated_at
    BEFORE UPDATE ON tools
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为users表创建更新时间戳触发器
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入一些测试数据
INSERT INTO users (username, email) VALUES 
    ('test_user', 'test@example.com'),
    ('admin_user', 'admin@example.com')
ON CONFLICT (username) DO NOTHING;

INSERT INTO tools (name, description, config) VALUES 
    ('file_reader', 'Read files from the filesystem', '{"allowed_extensions": [".txt", ".md", ".py", ".json"]}'),
    ('code_runner', 'Execute Python code in a sandboxed environment', '{"timeout": 30, "memory_limit": "512MB"}'),
    ('web_search', 'Search the web for information', '{"max_results": 10, "timeout": 15}')
ON CONFLICT (name) DO NOTHING;

-- 创建一些测试任务
INSERT INTO tasks (user_id, prompt, status) VALUES 
    ((SELECT id FROM users WHERE username = 'test_user'), 'Test task 1', 'COMPLETED'),
    ((SELECT id FROM users WHERE username = 'test_user'), 'Test task 2', 'RUNNING'),
    ((SELECT id FROM users WHERE username = 'admin_user'), 'Admin test task', 'QUEUED')
ON CONFLICT DO NOTHING;

-- 为测试任务创建一些日志
INSERT INTO logs (task_id, level, message, log_metadata) 
SELECT 
    t.id,
    'INFO',
    'Task started successfully',
    '{"trace_id": "test-trace-' || t.id || '", "agent": "test_agent"}'::jsonb
FROM tasks t
WHERE t.prompt LIKE 'Test task%'
ON CONFLICT DO NOTHING;
