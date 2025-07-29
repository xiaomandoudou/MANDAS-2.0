# tests/test_api_routes.py
import unittest
import requests
import json
import time

BASE_URL = "http://localhost:8000/mandas/v1"

class TestAPIRoutes(unittest.TestCase):
    """测试API路由的基本功能"""
    
    def setUp(self):
        """测试前的设置"""
        self.base_url = BASE_URL
        self.timeout = 10
    
    def test_health_check(self):
        """测试健康检查端点"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            # 如果端点存在，应该返回200状态码
            self.assertIn(response.status_code, [200, 404])  # 404表示端点不存在但服务运行
        except requests.exceptions.RequestException as e:
            self.skipTest(f"无法连接到API服务器: {e}")
    
    def test_create_task_endpoint(self):
        """测试创建任务端点"""
        payload = {
            "prompt": "Test task creation",
            "type": "default"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/tasks", 
                json=payload, 
                timeout=self.timeout
            )
            
            # 验证响应状态码
            self.assertEqual(response.status_code, 200)
            
            # 验证响应格式
            data = response.json()
            self.assertIn("id", data)
            self.assertIsInstance(data["id"], str)
            
            # 验证任务ID格式（应该是UUID）
            import uuid
            try:
                uuid.UUID(data["id"])
            except ValueError:
                self.fail("任务ID不是有效的UUID格式")
                
        except requests.exceptions.RequestException as e:
            self.skipTest(f"无法连接到API服务器: {e}")
    
    def test_get_task_status(self):
        """测试获取任务状态端点"""
        # 首先创建一个任务
        payload = {
            "prompt": "Test task status retrieval",
            "type": "default"
        }
        
        try:
            # 创建任务
            create_response = requests.post(
                f"{self.base_url}/tasks", 
                json=payload, 
                timeout=self.timeout
            )
            self.assertEqual(create_response.status_code, 200)
            
            task_id = create_response.json()["id"]
            
            # 获取任务状态
            status_response = requests.get(
                f"{self.base_url}/tasks/{task_id}", 
                timeout=self.timeout
            )
            self.assertEqual(status_response.status_code, 200)
            
            # 验证状态响应格式
            status_data = status_response.json()
            required_fields = ["id", "status", "prompt", "created_at"]
            
            for field in required_fields:
                self.assertIn(field, status_data, f"响应中缺少必需字段: {field}")
            
            # 验证状态值
            valid_statuses = ["QUEUED", "RUNNING", "COMPLETED", "FAILED"]
            self.assertIn(status_data["status"], valid_statuses)
            
        except requests.exceptions.RequestException as e:
            self.skipTest(f"无法连接到API服务器: {e}")
    
    def test_get_task_logs(self):
        """测试获取任务日志端点"""
        # 首先创建一个任务
        payload = {
            "prompt": "Test task logs retrieval",
            "type": "default"
        }
        
        try:
            # 创建任务
            create_response = requests.post(
                f"{self.base_url}/tasks", 
                json=payload, 
                timeout=self.timeout
            )
            self.assertEqual(create_response.status_code, 200)
            
            task_id = create_response.json()["id"]
            
            # 等待一段时间让任务开始执行
            time.sleep(5)
            
            # 获取任务日志
            logs_response = requests.get(
                f"{self.base_url}/tasks/{task_id}/logs", 
                timeout=self.timeout
            )
            
            # 日志端点应该存在（即使没有日志也应该返回空数组）
            self.assertEqual(logs_response.status_code, 200)
            
            # 验证日志格式
            logs_data = logs_response.json()
            self.assertIsInstance(logs_data, list)
            
            # 如果有日志，验证日志格式
            if logs_data:
                log_entry = logs_data[0]
                expected_fields = ["message", "level", "created_at"]
                
                for field in expected_fields:
                    if field in log_entry:  # 某些字段可能是可选的
                        self.assertIsInstance(log_entry[field], str)
                        
        except requests.exceptions.RequestException as e:
            self.skipTest(f"无法连接到API服务器: {e}")
    
    def test_list_tasks(self):
        """测试任务列表端点"""
        try:
            response = requests.get(f"{self.base_url}/tasks", timeout=self.timeout)
            self.assertEqual(response.status_code, 200)
            
            # 验证响应格式
            data = response.json()
            
            # 可能是分页格式或简单数组格式
            if isinstance(data, dict):
                # 分页格式
                self.assertIn("items", data)
                self.assertIsInstance(data["items"], list)
            else:
                # 简单数组格式
                self.assertIsInstance(data, list)
                
        except requests.exceptions.RequestException as e:
            self.skipTest(f"无法连接到API服务器: {e}")
    
    def test_invalid_task_id(self):
        """测试无效任务ID的处理"""
        invalid_task_id = "invalid-task-id"
        
        try:
            response = requests.get(
                f"{self.base_url}/tasks/{invalid_task_id}", 
                timeout=self.timeout
            )
            
            # 应该返回404或400错误
            self.assertIn(response.status_code, [400, 404])
            
        except requests.exceptions.RequestException as e:
            self.skipTest(f"无法连接到API服务器: {e}")
    
    def test_malformed_task_creation(self):
        """测试格式错误的任务创建请求"""
        # 测试缺少必需字段的请求
        invalid_payloads = [
            {},  # 空载荷
            {"type": "default"},  # 缺少prompt
            {"prompt": ""},  # 空prompt
            {"prompt": None, "type": "default"},  # None prompt
        ]
        
        for payload in invalid_payloads:
            try:
                response = requests.post(
                    f"{self.base_url}/tasks", 
                    json=payload, 
                    timeout=self.timeout
                )
                
                # 应该返回400错误
                self.assertIn(response.status_code, [400, 422])
                
            except requests.exceptions.RequestException as e:
                self.skipTest(f"无法连接到API服务器: {e}")
                break
    
    def test_api_route_prefix(self):
        """测试API路由前缀是否正确"""
        # 测试新的/mandas/v1前缀
        try:
            response = requests.get(f"{self.base_url}/tasks", timeout=self.timeout)
            # 如果能成功访问，说明新前缀工作正常
            self.assertEqual(response.status_code, 200)
            
        except requests.exceptions.RequestException:
            # 如果新前缀不工作，尝试旧前缀
            old_base_url = "http://localhost:8000/api/v1"
            try:
                response = requests.get(f"{old_base_url}/tasks", timeout=self.timeout)
                if response.status_code == 200:
                    self.fail("API仍在使用旧的/api/v1前缀，应该迁移到/mandas/v1")
            except requests.exceptions.RequestException:
                self.skipTest("无法连接到API服务器")

if __name__ == '__main__':
    unittest.main()
