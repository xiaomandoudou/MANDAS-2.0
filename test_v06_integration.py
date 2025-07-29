#!/usr/bin/env python3

import asyncio
import sys
import os

sys.path.append('/home/ubuntu/repos/MANDAS-2.0/services/agent-worker')

from app.core.tools.tool_registry import ToolRegistry
from app.core.security.execution_guard import ExecutionGuard
from app.memory.memory_manager import MemoryManager
from app.agents.router.llm_router_agent import LLMRouterAgent
from app.llm.llm_router import LLMRouter


async def test_v06_modules():
    print("🚀 开始测试MANDAS V0.6模块...")
    
    try:
        print("📋 测试ToolRegistry...")
        tool_registry = ToolRegistry("/home/ubuntu/repos/MANDAS-2.0/services/agent-worker/tools.d")
        await tool_registry.initialize()
        tools = tool_registry.list_tools()
        print(f"✅ ToolRegistry: 加载了 {len(tools)} 个工具")
        
        print("🧠 测试MemoryManager...")
        memory_manager = MemoryManager()
        await memory_manager.initialize()
        context = await memory_manager.get_context_for_llm("测试查询", "test_task")
        print(f"✅ MemoryManager: 获取上下文成功")
        
        print("🛡️ 测试ExecutionGuard...")
        execution_guard = ExecutionGuard(tool_registry)
        await execution_guard.initialize()
        print("✅ ExecutionGuard: 初始化成功")
        
        print("🧭 测试LLMRouterAgent...")
        llm_router = LLMRouter()
        await llm_router.initialize()
        llm_router_agent = LLMRouterAgent(llm_router)
        await llm_router_agent.initialize()
        print("✅ LLMRouterAgent: 初始化成功")
        
        print("🎉 所有V0.6模块测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_v06_modules())
    sys.exit(0 if success else 1)
