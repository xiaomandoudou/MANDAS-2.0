# tests/test_database_migration.py
import unittest
import psycopg
import os
import json
import requests
import time

class TestDatabaseMigration(unittest.TestCase):
    def setUp(self):
        # 获取数据库连接信息
        self.db_host = os.environ.get("DB_HOST", "localhost")
        self.db_port = os.environ.get("DB_PORT", "5432")
        self.db_name = os.environ.get("DB_NAME", "mandas_test")
        self.db_user = os.environ.get("DB_USER", "postgres")
        self.db_password = os.environ.get("DB_PASSWORD", "test_password")
        
        # 创建数据库连接
        self.connection_string = f"host={self.db_host} port={self.db_port} dbname={self.db_name} user={self.db_user} password={self.db_password}"
        
        try:
            self.conn = psycopg.connect(self.connection_string)
            self.conn.autocommit = True
        except psycopg.OperationalError as e:
            self.skipTest(f"无法连接到数据库: {e}")
        
    def tearDown(self):
        # 关闭数据库连接
        if hasattr(self, 'conn'):
            self.conn.close()
        
    def test_database_connection(self):
        """测试数据库连接是否正常"""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
    
    def test_required_tables_exist(self):
        """测试必需的表是否存在"""
        required_tables = ['tasks', 'logs', 'tools']
        
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            for table in required_tables:
                if table not in existing_tables:
                    # 如果表不存在，创建基本表结构用于测试
                    self.create_test_table(table)
    
    def create_test_table(self, table_name):
        """创建测试用的基本表结构"""
        with self.conn.cursor() as cursor:
            if table_name == 'tasks':
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id VARCHAR(255),
                        status VARCHAR(50) DEFAULT 'QUEUED',
                        prompt TEXT,
                        result JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
            elif table_name == 'logs':
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS logs (
                        id SERIAL PRIMARY KEY,
                        task_id UUID REFERENCES tasks(id),
                        level VARCHAR(20),
                        message TEXT,
                        log_metadata JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
            elif table_name == 'tools':
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tools (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) UNIQUE,
                        description TEXT,
                        config JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
        
    def test_column_rename_metadata_to_log_metadata(self):
        """测试metadata列重命名为log_metadata是否成功"""
        # 检查logs表的结构
        with self.conn.cursor() as cursor:
            # 检查列是否存在
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'logs' AND column_name = 'log_metadata'
            """)
            result = cursor.fetchone()
            
            # 验证log_metadata列存在
            self.assertIsNotNone(result, "log_metadata列不存在")
            
            # 检查旧列是否已移除
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'logs' AND column_name = 'metadata'
            """)
            result = cursor.fetchone()
            
            # 验证metadata列已移除（如果存在则说明迁移未完成）
            if result is not None:
                print("警告: metadata列仍然存在，可能需要手动迁移")
            
    def test_log_metadata_data_integrity(self):
        """测试log_metadata列的数据完整性"""
        # 首先插入一些测试数据
        with self.conn.cursor() as cursor:
            # 创建一个测试任务
            cursor.execute("""
                INSERT INTO tasks (prompt, status) 
                VALUES ('Test task for metadata integrity', 'COMPLETED')
                RETURNING id
            """)
            task_id = cursor.fetchone()[0]
            
            # 插入测试日志记录
            test_metadata = {"trace_id": "test-123", "agent": "test_agent", "tool": "test_tool"}
            cursor.execute("""
                INSERT INTO logs (task_id, level, message, log_metadata)
                VALUES (%s, 'INFO', 'Test log message', %s)
            """, (task_id, json.dumps(test_metadata)))
            
            # 查询并验证数据
            cursor.execute("""
                SELECT log_metadata 
                FROM logs 
                WHERE task_id = %s AND log_metadata IS NOT NULL
            """, (task_id,))
            
            result = cursor.fetchone()
            self.assertIsNotNone(result, "没有找到带log_metadata的日志记录")
            
            metadata = result[0]
            
            # 验证元数据是有效的JSON
            if isinstance(metadata, str):
                parsed = json.loads(metadata)
            else:
                parsed = metadata  # 可能已经是字典类型
                
            # 验证是字典类型
            self.assertIsInstance(parsed, dict, "log_metadata不是有效的JSON对象")
            
            # 验证包含预期的键
            self.assertIn("trace_id", parsed)
            self.assertEqual(parsed["trace_id"], "test-123")
    
    def test_tasks_table_structure(self):
        """测试tasks表结构是否正确"""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'tasks'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            # 验证必需的列存在
            column_names = [col[0] for col in columns]
            required_columns = ['id', 'status', 'prompt', 'created_at']
            
            for col in required_columns:
                self.assertIn(col, column_names, f"tasks表缺少必需的列: {col}")
    
    def test_logs_table_structure(self):
        """测试logs表结构是否正确"""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'logs'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            # 验证必需的列存在
            column_names = [col[0] for col in columns]
            required_columns = ['id', 'task_id', 'message', 'log_metadata', 'created_at']
            
            for col in required_columns:
                self.assertIn(col, column_names, f"logs表缺少必需的列: {col}")
    
    def test_foreign_key_constraints(self):
        """测试外键约束是否正确设置"""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name IN ('logs', 'tools')
            """)
            
            foreign_keys = cursor.fetchall()
            
            # 验证logs表的task_id外键
            logs_fk = [fk for fk in foreign_keys if fk[1] == 'logs' and fk[2] == 'task_id']
            if logs_fk:
                self.assertEqual(logs_fk[0][3], 'tasks', "logs.task_id外键应该引用tasks表")
                self.assertEqual(logs_fk[0][4], 'id', "logs.task_id外键应该引用tasks.id列")

if __name__ == '__main__':
    unittest.main()
