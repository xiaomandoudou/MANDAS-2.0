#!/usr/bin/env python3
"""Debug code execution issue in functional tests"""

import asyncio
import sys
import os

sys.path.append('/home/ubuntu/repos/MANDAS-2.0/services/agent-worker')

from app.core.tools.tool_registry import ToolRegistry
from app.core.security.execution_guard import ExecutionGuard


async def debug_code_execution():
    """Debug the code execution failure"""
    print("🔍 Debugging code execution issue...")
    
    tool_registry = ToolRegistry("/home/ubuntu/repos/MANDAS-2.0/services/agent-worker/tools.d")
    await tool_registry.initialize()
    
    execution_guard = ExecutionGuard(tool_registry)
    await execution_guard.initialize()
    
    simple_code = """
print("Hello from Python!")
result = 2 + 2
print(f"2 + 2 = {result}")
"""
    
    print("Testing simple code execution...")
    result = await execution_guard.execute_tool(
        "python_executor",
        {"code": simple_code},
        {"task_id": "debug_test", "user_id": "test"}
    )
    
    print(f"Simple code result: {result}")
    
    if not result.get("success"):
        print(f"❌ Simple code execution failed: {result.get('error')}")
        return False
    
    fibonacci_code = """
def fibonacci(n):
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib[:n]

result = fibonacci(10)
print("Fibonacci sequence first 10 terms:", result)

with open('/tmp/fibonacci.txt', 'w') as f:
    f.write(str(result))
print("Results saved to file")
"""
    
    print("Testing fibonacci code execution...")
    result = await execution_guard.execute_tool(
        "python_executor",
        {"code": fibonacci_code},
        {"task_id": "debug_fibonacci", "user_id": "test"}
    )
    
    print(f"Fibonacci code result: {result}")
    
    if result.get("success"):
        print("✅ Code execution working correctly")
        return True
    else:
        print(f"❌ Fibonacci code execution failed: {result.get('error')}")
        return False


if __name__ == "__main__":
    success = asyncio.run(debug_code_execution())
    sys.exit(0 if success else 1)
