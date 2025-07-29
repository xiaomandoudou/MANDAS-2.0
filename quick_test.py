#!/usr/bin/env python3
"""
快速测试脚本 - 验证测试环境和基本功能
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    version = sys.version_info
    print(f"   Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False
    
    print("✅ Python版本符合要求")
    return True

def check_required_packages():
    """检查必需的包"""
    print("\n📦 检查必需的包...")
    
    required_packages = [
        "pytest",
        "requests", 
        "websocket",
        "psycopg"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == "websocket":
                # websocket-client包导入名称是websocket
                __import__("websocket")
            elif package == "psycopg":
                # psycopg3的导入名称是psycopg
                __import__("psycopg")
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (未安装)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  缺少包: {', '.join(missing_packages)}")
        print("请运行以下命令安装:")
        if "websocket" in missing_packages:
            missing_packages[missing_packages.index("websocket")] = "websocket-client"
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有必需包已安装")
    return True

def check_test_files():
    """检查测试文件"""
    print("\n📁 检查测试文件...")
    
    test_files = [
        "tests/test_end_to_end.py",
        "tests/test_database_migration.py", 
        "tests/test_api_routes.py",
        "tests/test_agent_abstractions.py"
    ]
    
    missing_files = []
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"✅ {test_file}")
        else:
            print(f"❌ {test_file} (不存在)")
            missing_files.append(test_file)
    
    if missing_files:
        print(f"\n⚠️  缺少测试文件: {len(missing_files)} 个")
        return False
    
    print("✅ 所有测试文件存在")
    return True

def check_github_actions():
    """检查GitHub Actions配置"""
    print("\n🔧 检查GitHub Actions配置...")
    
    workflow_file = ".github/workflows/ci.yml"
    
    if Path(workflow_file).exists():
        print(f"✅ {workflow_file}")
        
        # 检查工作流文件内容
        with open(workflow_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "MANDAS-2.0 CI/CD Pipeline" in content:
            print("✅ 工作流配置正确")
        else:
            print("⚠️  工作流配置可能有问题")
            
        return True
    else:
        print(f"❌ {workflow_file} (不存在)")
        return False

def run_syntax_check():
    """运行语法检查"""
    print("\n🔍 运行Python语法检查...")
    
    test_files = [
        "tests/test_end_to_end.py",
        "tests/test_database_migration.py",
        "tests/test_api_routes.py", 
        "tests/test_agent_abstractions.py"
    ]
    
    all_valid = True
    
    for test_file in test_files:
        if not Path(test_file).exists():
            continue
            
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            compile(code, test_file, 'exec')
            print(f"✅ {test_file} 语法正确")
            
        except SyntaxError as e:
            print(f"❌ {test_file} 语法错误: {e}")
            all_valid = False
        except Exception as e:
            print(f"⚠️  {test_file} 检查失败: {e}")
    
    return all_valid

def run_import_test():
    """运行导入测试"""
    print("\n📥 测试模块导入...")
    
    # 测试标准库导入
    try:
        import unittest
        import json
        import time
        import threading
        import queue
        print("✅ 标准库导入正常")
    except ImportError as e:
        print(f"❌ 标准库导入失败: {e}")
        return False
    
    # 测试第三方库导入
    try:
        import requests
        import websocket
        print("✅ 第三方库导入正常")
    except ImportError as e:
        print(f"❌ 第三方库导入失败: {e}")
        return False
    
    return True

def check_docker_availability():
    """检查Docker可用性"""
    print("\n🐳 检查Docker可用性...")
    
    try:
        result = subprocess.run(
            ["docker", "--version"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"✅ Docker可用: {result.stdout.strip()}")
            
            # 检查Docker是否运行
            result = subprocess.run(
                ["docker", "info"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                print("✅ Docker服务正在运行")
                return True
            else:
                print("⚠️  Docker已安装但服务未运行")
                return False
        else:
            print("❌ Docker命令执行失败")
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Docker未安装或不可用")
        return False

def run_basic_test():
    """运行基本测试"""
    print("\n🧪 运行基本测试...")
    
    try:
        # 运行一个简单的pytest命令来验证测试框架
        result = subprocess.run(
            ["python", "-m", "pytest", "--version"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ pytest可用: {result.stdout.strip()}")
            
            # 尝试运行测试发现
            result = subprocess.run(
                ["python", "-m", "pytest", "--collect-only", "tests/"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ 测试发现成功")
                return True
            else:
                print("⚠️  测试发现有问题")
                print(result.stderr)
                return False
        else:
            print("❌ pytest不可用")
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"❌ 测试运行失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 MANDAS-2.0 测试环境快速检查")
    print("=" * 50)
    
    checks = [
        ("Python版本", check_python_version),
        ("必需包", check_required_packages),
        ("测试文件", check_test_files),
        ("GitHub Actions", check_github_actions),
        ("语法检查", run_syntax_check),
        ("模块导入", run_import_test),
        ("Docker可用性", check_docker_availability),
        ("基本测试", run_basic_test),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
        except Exception as e:
            print(f"❌ {name} 检查失败: {e}")
    
    print(f"\n📊 检查结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有检查通过！测试环境准备就绪。")
        print("\n下一步:")
        print("1. 运行 python run_tests.sh 执行完整测试")
        print("2. 或运行 python check_github_status.py 1 检查PR状态")
        return True
    else:
        print("⚠️  部分检查未通过，请解决上述问题后重试。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
