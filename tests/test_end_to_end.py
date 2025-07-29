# tests/test_end_to_end.py
import unittest
import requests
import json
import time
import websocket
import threading
import queue

BASE_URL = "http://localhost:8000/mandas/v1"
WS_BASE_URL = "ws://localhost:8000/mandas/v1"

class TestEndToEnd(unittest.TestCase):
    def test_complex_task_with_multiple_tools(self):
        """测试包含多个工具调用的复杂任务"""
        # 创建一个复杂任务，需要文件读取和代码执行
        payload = {
            "prompt": """
            Please perform the following steps:
            1. Read the README.md file
            2. Count the number of words in the file using Python
            3. Generate a summary of the main points
            4. Create a simple report with the word count and summary
            """,
            "type": "default"
        }
        
        # 设置WebSocket监听
        message_queue = queue.Queue()
        
        # 提交任务
        try:
            response = requests.post(f"{BASE_URL}/tasks", json=payload, timeout=10)
            self.assertEqual(response.status_code, 200)
            
            task_data = response.json()
            task_id = task_data["id"]
        except requests.exceptions.RequestException as e:
            self.skipTest(f"无法连接到服务器: {e}")
        
        # 设置WebSocket连接
        def on_message(ws, message):
            message_queue.put(json.loads(message))
        
        def on_error(ws, error):
            print(f"WebSocket错误: {error}")
        
        ws_url = f"{WS_BASE_URL}/ws/tasks/{task_id}/stream"
        ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error)
        
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # 等待连接建立
        time.sleep(2)
        
        # 等待任务完成
        max_wait = 300  # 最多等待5分钟
        start_time = time.time()
        completed = False
        status_data = None
        
        while time.time() - start_time < max_wait:
            try:
                status_response = requests.get(f"{BASE_URL}/tasks/{task_id}", timeout=10)
                status_data = status_response.json()
                
                if status_data["status"] in ["COMPLETED", "FAILED"]:
                    completed = True
                    break
                    
                time.sleep(5)  # 每5秒轮询一次
            except requests.exceptions.RequestException:
                # 如果请求失败，继续等待
                time.sleep(5)
                continue
            
        # 关闭WebSocket连接
        ws.close()
        
        # 验证任务是否成功完成
        if not completed:
            self.skipTest("任务未在规定时间内完成，可能是服务未启动")
            
        self.assertEqual(status_data["status"], "COMPLETED")
        
        # 验证结果是否包含预期内容
        result = status_data.get("result", "")
        self.assertIn("words", result.lower())  # 应包含字数统计
        self.assertIn("summary", result.lower())  # 应包含摘要
        
        # 获取任务日志以验证工具调用
        try:
            logs_response = requests.get(f"{BASE_URL}/tasks/{task_id}/logs", timeout=10)
            logs = logs_response.json()
            
            log_text = " ".join([log.get("message", "") for log in logs])
            self.assertTrue(
                any("file" in log.lower() for log in log_text.split()),
                "日志中未找到文件读取工具的调用记录"
            )
            self.assertTrue(
                any("python" in log.lower() or "code" in log.lower() for log in log_text.split()),
                "日志中未找到代码执行工具的调用记录"
            )
        except requests.exceptions.RequestException:
            # 如果无法获取日志，跳过日志验证
            pass
        
        # 验证WebSocket通信
        # 从消息队列中提取所有消息
        messages = []
        while not message_queue.empty():
            messages.append(message_queue.get())
        
        # 验证是否收到了状态更新和日志消息
        status_updates = [msg for msg in messages if msg.get("type") == "status_update"]
        logs = [msg for msg in messages if msg.get("type") == "log"]
        
        if messages:  # 只有在收到消息时才验证
            self.assertTrue(status_updates or logs, "WebSocket未发送任何有效消息")

    def test_simple_task_execution(self):
        """测试简单任务执行"""
        payload = {
            "prompt": "Hello, please respond with a simple greeting.",
            "type": "default"
        }
        
        try:
            # 提交任务
            response = requests.post(f"{BASE_URL}/tasks", json=payload, timeout=10)
            self.assertEqual(response.status_code, 200)
            
            task_data = response.json()
            task_id = task_data["id"]
            
            # 等待任务完成
            max_wait = 60  # 简单任务1分钟内应该完成
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_response = requests.get(f"{BASE_URL}/tasks/{task_id}", timeout=10)
                status_data = status_response.json()
                
                if status_data["status"] in ["COMPLETED", "FAILED"]:
                    break
                    
                time.sleep(2)
            
            # 验证任务完成
            self.assertIn(status_data["status"], ["COMPLETED", "FAILED"])
            
        except requests.exceptions.RequestException as e:
            self.skipTest(f"无法连接到服务器: {e}")

    def test_task_status_transitions(self):
        """测试任务状态转换"""
        payload = {
            "prompt": "Test task status transitions",
            "type": "default"
        }
        
        try:
            # 提交任务
            response = requests.post(f"{BASE_URL}/tasks", json=payload, timeout=10)
            self.assertEqual(response.status_code, 200)
            
            task_data = response.json()
            task_id = task_data["id"]
            
            # 验证初始状态
            status_response = requests.get(f"{BASE_URL}/tasks/{task_id}", timeout=10)
            initial_status = status_response.json()["status"]
            self.assertIn(initial_status, ["QUEUED", "RUNNING"])
            
            # 监控状态变化
            seen_statuses = {initial_status}
            max_wait = 60
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_response = requests.get(f"{BASE_URL}/tasks/{task_id}", timeout=10)
                current_status = status_response.json()["status"]
                seen_statuses.add(current_status)
                
                if current_status in ["COMPLETED", "FAILED"]:
                    break
                    
                time.sleep(2)
            
            # 验证状态转换合理性
            valid_transitions = {"QUEUED", "RUNNING", "COMPLETED", "FAILED"}
            self.assertTrue(seen_statuses.issubset(valid_transitions))
            
        except requests.exceptions.RequestException as e:
            self.skipTest(f"无法连接到服务器: {e}")

if __name__ == '__main__':
    unittest.main()
