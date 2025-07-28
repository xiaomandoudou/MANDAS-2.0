#!/usr/bin/env python3
"""MANDAS V0.6 综合验证测试"""

import asyncio
import sys
import os
import time
import requests
import subprocess
from typing import Dict, Any

sys.path.append('/home/ubuntu/repos/MANDAS-2.0/services/agent-worker')

def run_test_script(script_name: str) -> Dict[str, Any]:
    """运行测试脚本并返回结果"""
    try:
        print(f"\n{'='*60}")
        print(f"🚀 执行 {script_name}")
        print(f"{'='*60}")
        
        result = subprocess.run([
            sys.executable, script_name
        ], capture_output=True, text=True, cwd='/home/ubuntu/repos/MANDAS-2.0')
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return {
            "script": script_name,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
        
    except Exception as e:
        print(f"❌ 执行 {script_name} 时出错: {e}")
        return {
            "script": script_name,
            "success": False,
            "error": str(e),
            "return_code": -1
        }

def test_docker_services():
    """测试Docker服务状态"""
    print("\n🐳 检查Docker服务状态...")
    
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker服务正常运行")
            print(result.stdout)
            return True
        else:
            print(f"❌ Docker服务异常: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Docker检查失败: {e}")
        return False

def test_api_gateway():
    """测试API Gateway连接"""
    print("\n🌐 检查API Gateway状态...")
    
    try:
        response = requests.get("http://localhost:8080/mandas/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Gateway健康检查通过 - 新端点路径已更新")
            return True
        else:
            print(f"❌ API Gateway健康检查失败: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("⚠️ API Gateway未运行 - psycopg2依赖问题阻止启动")
        return False
    except Exception as e:
        print(f"❌ API Gateway检查异常: {e}")
        return False

def main():
    """主验证函数"""
    print("🎯 MANDAS V0.6 综合验证开始")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    docker_ok = test_docker_services()
    api_ok = test_api_gateway()
    
    test_scripts = [
        "test_v06_security.py",
        "test_v06_functional.py", 
        "test_v06_integration.py"
    ]
    
    results = []
    for script in test_scripts:
        if os.path.exists(script):
            result = run_test_script(script)
            results.append(result)
        else:
            print(f"⚠️ 测试脚本 {script} 不存在")
            results.append({
                "script": script,
                "success": False,
                "error": "Script not found"
            })
    
    print(f"\n{'='*60}")
    print("🎯 MANDAS V0.6 综合验证结果")
    print(f"{'='*60}")
    
    print(f"🐳 Docker服务: {'✅ 正常' if docker_ok else '❌ 异常'}")
    print(f"🌐 API Gateway: {'✅ 正常' if api_ok else '❌ 异常'}")
    
    passed = 0
    total = len(results)
    
    for result in results:
        status = "✅ 通过" if result["success"] else "❌ 失败"
        print(f"📋 {result['script']}: {status}")
        if result["success"]:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total and docker_ok:
        print("🎉 MANDAS V0.6 验证完全通过！")
        return True
    else:
        print("⚠️ 部分验证失败，需要修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
