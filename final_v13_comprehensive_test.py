#!/usr/bin/env python3
import asyncio
import aiohttp
import json
from datetime import datetime
import time

async def final_v13_comprehensive_test():
    """Final comprehensive V1.3 test to achieve 100% success rate"""
    print("=== MANDAS V1.3 Final Comprehensive Test ===")
    print(f"Timestamp: {datetime.now()}")
    
    results = {
        "authentication": False,
        "task_creation": False, 
        "plan_generation": False,
        "websocket_connection": False,
        "real_time_updates": False,
        "task_completion": False
    }
    
    token = None
    task_id = None
    
    async with aiohttp.ClientSession() as session:
        
        print(f"\n=== Testing Authentication Flow ===")
        try:
            auth_data = aiohttp.FormData()
            auth_data.add_field('username', 'testuser')
            auth_data.add_field('password', 'testpass')
            
            async with session.post(
                "http://localhost:8081/mandas/v1/auth/login",
                data=auth_data
            ) as response:
                if response.status == 200:
                    auth_result = await response.json()
                    token = auth_result.get('access_token')
                    if token:
                        print(f"✅ Authentication successful, token obtained")
                        results["authentication"] = True
                    else:
                        print(f"❌ Authentication failed: No token in response")
                else:
                    error_text = await response.text()
                    print(f"❌ Authentication failed: {response.status} - {error_text}")
        except Exception as e:
            print(f"❌ Authentication error: {e}")
        
        if not token:
            print(f"❌ Cannot proceed without authentication token")
            return results
        
        headers = {"Authorization": f"Bearer {token}"}
        
        print(f"\n=== Testing Task Creation ===")
        try:
            task_data = {
                "prompt": "创建一个Python数据分析脚本，分析销售数据并生成可视化图表",
                "config": {"complexity": "medium", "priority": 1}
            }
            
            async with session.post(
                "http://localhost:8081/mandas/v1/tasks/",
                headers=headers,
                json=task_data
            ) as response:
                if response.status in [200, 201, 202]:
                    task_result = await response.json()
                    task_id = task_result.get('task_id') or task_result.get('id')
                    if task_id:
                        print(f"✅ Task created successfully: {task_id}")
                        results["task_creation"] = True
                    else:
                        print(f"❌ Task creation failed: No task_id in response")
                else:
                    error_text = await response.text()
                    print(f"❌ Task creation failed: {response.status} - {error_text}")
        except Exception as e:
            print(f"❌ Task creation error: {e}")
        
        if not task_id:
            print(f"❌ Cannot proceed without task_id")
            return results
        
        print(f"\n=== Testing Plan Generation ===")
        try:
            await asyncio.sleep(3)
            
            async with session.get(
                f"http://localhost:8081/mandas/v1/tasks/{task_id}/plan",
                headers=headers
            ) as response:
                if response.status == 200:
                    plan_result = await response.json()
                    if plan_result.get('plan') or plan_result.get('summary'):
                        print(f"✅ Plan generation successful")
                        print(f"   Plan summary: {plan_result.get('summary', 'Plan available')}")
                        results["plan_generation"] = True
                    else:
                        print(f"❌ Plan generation failed: No plan data")
                else:
                    error_text = await response.text()
                    print(f"❌ Plan generation failed: {response.status} - {error_text}")
        except Exception as e:
            print(f"❌ Plan generation error: {e}")
        
        print(f"\n=== Testing WebSocket Connection ===")
        try:
            import websockets
            
            ws_url = f"ws://localhost:8081/mandas/v1/tasks/{task_id}/stream"
            
            async with websockets.connect(ws_url) as websocket:
                print(f"✅ WebSocket connection established")
                results["websocket_connection"] = True
                
                print(f"   Waiting for real-time updates...")
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    print(f"✅ Real-time update received: {data.get('type', 'unknown')}")
                    results["real_time_updates"] = True
                except asyncio.TimeoutError:
                    print(f"⚠️ No real-time updates received within timeout")
                except Exception as e:
                    print(f"⚠️ Real-time update error: {e}")
                    
        except ImportError:
            print(f"⚠️ WebSocket test skipped: websockets library not available")
        except Exception as e:
            print(f"❌ WebSocket connection error: {e}")
        
        print(f"\n=== Testing Task Completion ===")
        try:
            for attempt in range(3):
                await asyncio.sleep(5)
                
                async with session.get(
                    f"http://localhost:8081/mandas/v1/tasks/{task_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        task_status = await response.json()
                        status = task_status.get('status', 'UNKNOWN')
                        print(f"   Attempt {attempt + 1}: Task status = {status}")
                        
                        if status in ['COMPLETED', 'SUCCESS']:
                            print(f"✅ Task completed successfully")
                            results["task_completion"] = True
                            break
                        elif status in ['FAILED', 'ERROR']:
                            print(f"❌ Task failed")
                            break
                        elif status in ['RUNNING', 'PROCESSING']:
                            print(f"   Task still running...")
                            continue
                    else:
                        print(f"   Status check failed: {response.status}")
            
            if not results["task_completion"]:
                print(f"⚠️ Task completion not verified within test timeframe")
                
        except Exception as e:
            print(f"❌ Task completion check error: {e}")
    
    print(f"\n=== Final Test Results ===")
    passed_tests = sum(results.values())
    total_tests = len(results)
    success_rate = (passed_tests / total_tests) * 100
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate == 100.0:
        print(f"🎉 ALL TESTS PASSED! V1.3 system fully functional!")
    elif success_rate >= 80.0:
        print(f"✅ Core functionality working, minor issues remain")
    else:
        print(f"❌ Significant issues detected, requires investigation")
    
    return results

if __name__ == "__main__":
    asyncio.run(final_v13_comprehensive_test())
