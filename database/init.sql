
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'QUEUED',
    prompt TEXT NOT NULL,
    plan JSONB,
    result JSONB,
    logs TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    retry_count INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 5,
    config JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS tools_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    function_schema JSONB NOT NULL,
    api_endpoint VARCHAR(500),
    permissions TEXT[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_base_docs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    mime_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'PROCESSING',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS llm_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    model_type VARCHAR(100) NOT NULL, -- 'ollama', 'qwen3-gguf', etc.
    endpoint_url VARCHAR(500),
    capabilities TEXT[],
    max_tokens INTEGER,
    cost_per_token DECIMAL(10, 8),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS task_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    trace_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_task_logs_task_id ON task_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_task_logs_trace_id ON task_logs(trace_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_docs_user_id ON knowledge_base_docs(user_id);

INSERT INTO users (id, username, email, password_hash) VALUES 
('00000000-0000-0000-0000-000000000001', 'admin', 'admin@mandas.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5S/kS') -- password: admin123
ON CONFLICT (username) DO NOTHING;

INSERT INTO tools_registry (name, description, function_schema, permissions) VALUES 
(
    'echo',
    'Simple echo tool for testing Docker sandbox execution',
    '{"type": "function", "function": {"name": "echo", "description": "Echo the input text", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to echo"}}, "required": ["text"]}}}',
    ARRAY['read']
),
(
    'python_executor',
    'Execute Python code in Docker sandbox',
    '{"type": "function", "function": {"name": "python_executor", "description": "Execute Python code safely", "parameters": {"type": "object", "properties": {"code": {"type": "string", "description": "Python code to execute"}}, "required": ["code"]}}}',
    ARRAY['execute', 'read', 'write']
),
(
    'shell_executor',
    'Execute shell commands in Docker sandbox',
    '{"type": "function", "function": {"name": "shell_executor", "description": "Execute shell commands safely", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "Shell command to execute"}}, "required": ["command"]}}}',
    ARRAY['execute', 'read', 'write']
)
ON CONFLICT (name) DO NOTHING;

INSERT INTO llm_models (name, model_type, endpoint_url, capabilities, max_tokens) VALUES 
(
    'llama3-8b',
    'ollama',
    'http://ollama:11434',
    ARRAY['chat', 'completion', 'reasoning'],
    8192
),
(
    'qwen3-gguf',
    'qwen3-gguf',
    'http://localhost:8001',
    ARRAY['chat', 'completion', 'coding', 'reasoning'],
    32768
)
ON CONFLICT (name) DO NOTHING;
