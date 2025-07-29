#!/usr/bin/env python3
"""
MANDAS V1.3 TaskPlanner 集成示例
演示如何在实际场景中使用TaskPlanner模块
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# 添加路径以导入MANDAS模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'agent-worker'))

from app.core.planning.planner import TaskPlanner, TaskPlan
from app.core.agents.planner_agent import PlannerAgent


class MockLLMClient:
    """模拟LLM客户端，用于演示"""
    
    async def generate(self, prompt: str) -> str:
        """模拟LLM生成响应"""
        print(f"🤖 LLM收到Prompt (长度: {len(prompt)} 字符)")
        
        # 根据prompt内容返回不同的计划
        if "文件分析" in prompt or "读取文件" in prompt:
            return self._generate_file_analysis_plan()
        elif "数据处理" in prompt or "计算" in prompt:
            return self._generate_data_processing_plan()
        elif "网页爬取" in prompt or "爬虫" in prompt:
            return self._generate_web_scraping_plan()
        else:
            return self._generate_simple_plan()
    
    def _generate_file_analysis_plan(self) -> str:
        """生成文件分析计划"""
        return '''
        {
            "steps": [
                {
                    "step_id": 1,
                    "name": "读取文件",
                    "description": "读取指定的文本文件内容",
                    "tool_name": "file_reader",
                    "tool_parameters": {
                        "file_path": "@{user_input.file_path}"
                    },
                    "dependencies": []
                },
                {
                    "step_id": 2,
                    "name": "文本预处理",
                    "description": "清理和预处理文本内容",
                    "tool_name": "text_processor",
                    "tool_parameters": {
                        "text": "@{steps.1.result}",
                        "operations": ["remove_whitespace", "normalize"]
                    },
                    "dependencies": [1]
                },
                {
                    "step_id": 3,
                    "name": "内容分析",
                    "description": "分析文本内容，提取关键信息",
                    "tool_name": "text_analyzer",
                    "tool_parameters": {
                        "text": "@{steps.2.result}",
                        "analysis_type": "comprehensive"
                    },
                    "dependencies": [2]
                },
                {
                    "step_id": 4,
                    "name": "生成报告",
                    "description": "基于分析结果生成报告",
                    "tool_name": "report_generator",
                    "tool_parameters": {
                        "analysis_result": "@{steps.3.result}",
                        "format": "markdown"
                    },
                    "dependencies": [3]
                }
            ]
        }
        '''
    
    def _generate_data_processing_plan(self) -> str:
        """生成数据处理计划"""
        return '''
        {
            "steps": [
                {
                    "step_id": 1,
                    "name": "加载数据",
                    "description": "从数据源加载数据",
                    "tool_name": "data_loader",
                    "tool_parameters": {
                        "source": "@{user_input.data_source}",
                        "format": "csv"
                    },
                    "dependencies": []
                },
                {
                    "step_id": 2,
                    "name": "数据清洗",
                    "description": "清洗和预处理数据",
                    "tool_name": "data_cleaner",
                    "tool_parameters": {
                        "data": "@{steps.1.result}",
                        "remove_nulls": true,
                        "normalize": true
                    },
                    "dependencies": [1]
                },
                {
                    "step_id": 3,
                    "name": "统计分析",
                    "description": "进行统计分析",
                    "tool_name": "statistical_analyzer",
                    "tool_parameters": {
                        "data": "@{steps.2.result}",
                        "methods": ["mean", "median", "std", "correlation"]
                    },
                    "dependencies": [2]
                },
                {
                    "step_id": 4,
                    "name": "可视化",
                    "description": "创建数据可视化图表",
                    "tool_name": "data_visualizer",
                    "tool_parameters": {
                        "data": "@{steps.2.result}",
                        "stats": "@{steps.3.result}",
                        "chart_types": ["histogram", "scatter", "correlation_matrix"]
                    },
                    "dependencies": [2, 3]
                }
            ]
        }
        '''
    
    def _generate_web_scraping_plan(self) -> str:
        """生成网页爬取计划"""
        return '''
        {
            "steps": [
                {
                    "step_id": 1,
                    "name": "获取网页内容",
                    "description": "爬取指定网页的HTML内容",
                    "tool_name": "web_scraper",
                    "tool_parameters": {
                        "url": "@{user_input.target_url}",
                        "headers": {"User-Agent": "MANDAS-Bot/1.3"}
                    },
                    "dependencies": []
                },
                {
                    "step_id": 2,
                    "name": "解析HTML",
                    "description": "解析HTML内容，提取结构化数据",
                    "tool_name": "html_parser",
                    "tool_parameters": {
                        "html": "@{steps.1.result}",
                        "selectors": "@{user_input.css_selectors}"
                    },
                    "dependencies": [1]
                },
                {
                    "step_id": 3,
                    "name": "数据验证",
                    "description": "验证提取的数据质量",
                    "tool_name": "data_validator",
                    "tool_parameters": {
                        "data": "@{steps.2.result}",
                        "rules": ["not_empty", "valid_format"]
                    },
                    "dependencies": [2]
                },
                {
                    "step_id": 4,
                    "name": "保存数据",
                    "description": "将验证后的数据保存到文件",
                    "tool_name": "file_writer",
                    "tool_parameters": {
                        "data": "@{steps.3.result}",
                        "file_path": "@{user_input.output_file}",
                        "format": "json"
                    },
                    "dependencies": [3]
                }
            ]
        }
        '''
    
    def _generate_simple_plan(self) -> str:
        """生成简单计划"""
        return '''
        {
            "steps": [
                {
                    "step_id": 1,
                    "name": "执行任务",
                    "description": "执行用户请求的任务",
                    "tool_name": "general_executor",
                    "tool_parameters": {
                        "task": "@{user_input.task_description}"
                    },
                    "dependencies": []
                }
            ]
        }
        '''


async def demo_task_planner_basic():
    """演示TaskPlanner的基本功能"""
    print("\n" + "="*60)
    print("🎯 演示1: TaskPlanner基本功能")
    print("="*60)
    
    # 创建模拟的LLM客户端和TaskPlanner
    llm_client = MockLLMClient()
    planner = TaskPlanner(llm_client)
    
    # 模拟可用工具
    available_tools = [
        {
            "name": "file_reader",
            "description": "读取文件内容",
            "category": "file_system",
            "parameters": {
                "file_path": {"type": "string", "description": "文件路径"}
            }
        },
        {
            "name": "text_processor",
            "description": "处理文本内容",
            "category": "text_processing",
            "parameters": {
                "text": {"type": "string", "description": "要处理的文本"},
                "operations": {"type": "array", "description": "处理操作列表"}
            }
        },
        {
            "name": "text_analyzer",
            "description": "分析文本内容",
            "category": "analysis",
            "parameters": {
                "text": {"type": "string", "description": "要分析的文本"},
                "analysis_type": {"type": "string", "description": "分析类型"}
            }
        },
        {
            "name": "report_generator",
            "description": "生成报告",
            "category": "output",
            "parameters": {
                "analysis_result": {"type": "object", "description": "分析结果"},
                "format": {"type": "string", "description": "报告格式"}
            }
        }
    ]
    
    # 创建任务计划
    task_description = "请帮我分析一个文本文件的内容，并生成分析报告"
    task_id = f"demo-task-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    try:
        print(f"📝 任务描述: {task_description}")
        print(f"🆔 任务ID: {task_id}")
        print(f"🔧 可用工具数量: {len(available_tools)}")
        
        plan = await planner.create_plan(
            task_description=task_description,
            task_id=task_id,
            available_tools=available_tools
        )
        
        print(f"\n✅ 计划生成成功!")
        print(f"📋 计划ID: {plan.plan_id}")
        print(f"📊 步骤数量: {len(plan.steps)}")
        print(f"⏰ 创建时间: {plan.created_at}")
        
        print(f"\n📋 执行步骤详情:")
        for i, step in enumerate(plan.steps, 1):
            print(f"  {i}. {step.name}")
            print(f"     描述: {step.description}")
            print(f"     工具: {step.tool_name}")
            print(f"     依赖: {step.dependencies if step.dependencies else '无'}")
            if step.tool_parameters:
                print(f"     参数: {json.dumps(step.tool_parameters, ensure_ascii=False, indent=8)}")
            print()
        
        return plan
        
    except Exception as e:
        print(f"❌ 计划生成失败: {e}")
        return None


async def demo_planner_agent():
    """演示PlannerAgent的功能"""
    print("\n" + "="*60)
    print("🤖 演示2: PlannerAgent集成功能")
    print("="*60)
    
    # 创建PlannerAgent
    llm_client = MockLLMClient()
    config = {
        "max_retry_attempts": 3,
        "enable_plan_optimization": True
    }
    agent = PlannerAgent(llm_client, config)
    
    # 初始化代理
    await agent.initialize()
    
    # 检查代理能力
    capabilities = await agent.get_capabilities()
    print(f"🔍 代理能力:")
    for key, value in capabilities.items():
        print(f"  - {key}: {value}")
    
    # 健康检查
    health = await agent.health_check()
    print(f"\n💊 健康状态: {'✅ 健康' if health['healthy'] else '❌ 异常'}")
    
    # 执行任务规划
    task_input = {
        "task_id": f"agent-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "prompt": "我需要处理一批CSV数据文件，进行统计分析并生成可视化图表",
        "context": {
            "user_id": "demo_user",
            "priority": "high"
        }
    }
    
    print(f"\n📝 执行任务规划...")
    print(f"任务ID: {task_input['task_id']}")
    print(f"任务描述: {task_input['prompt']}")
    
    result = await agent._execute(task_input)
    
    if result["success"]:
        print(f"\n✅ 任务规划成功!")
        print(f"📋 计划ID: {result['plan_id']}")
        print(f"📊 步骤数量: {result['steps_count']}")
        print(f"💬 消息: {result['message']}")
        
        # 显示计划详情
        plan_data = result["plan"]
        print(f"\n📋 计划详情:")
        for step in plan_data["steps"]:
            print(f"  步骤 {step['step_id']}: {step['name']}")
            print(f"    工具: {step['tool_name']}")
            print(f"    依赖: {step['dependencies'] if step['dependencies'] else '无'}")
        
        return result
    else:
        print(f"❌ 任务规划失败: {result['error']}")
        return None


async def demo_complex_scenarios():
    """演示复杂场景的任务规划"""
    print("\n" + "="*60)
    print("🌟 演示3: 复杂场景任务规划")
    print("="*60)
    
    llm_client = MockLLMClient()
    agent = PlannerAgent(llm_client)
    await agent.initialize()
    
    # 场景1: 网页数据爬取和分析
    scenarios = [
        {
            "name": "网页数据爬取",
            "prompt": "请帮我爬取电商网站的产品信息，并保存为结构化数据",
            "expected_tools": ["web_scraper", "html_parser", "data_validator", "file_writer"]
        },
        {
            "name": "文档智能分析",
            "prompt": "分析一批PDF文档，提取关键信息并生成摘要报告",
            "expected_tools": ["file_reader", "text_processor", "text_analyzer", "report_generator"]
        },
        {
            "name": "数据科学流水线",
            "prompt": "构建一个完整的数据科学流水线，包括数据加载、清洗、分析和可视化",
            "expected_tools": ["data_loader", "data_cleaner", "statistical_analyzer", "data_visualizer"]
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📊 场景 {i}: {scenario['name']}")
        print(f"描述: {scenario['prompt']}")
        
        task_input = {
            "task_id": f"scenario-{i}-{datetime.now().strftime('%H%M%S')}",
            "prompt": scenario["prompt"]
        }
        
        result = await agent._execute(task_input)
        
        if result["success"]:
            plan_data = result["plan"]
            used_tools = [step["tool_name"] for step in plan_data["steps"]]
            
            print(f"✅ 规划成功 - {result['steps_count']} 个步骤")
            print(f"🔧 使用工具: {', '.join(used_tools)}")
            
            # 检查是否使用了预期的工具
            expected_found = sum(1 for tool in scenario["expected_tools"] if tool in used_tools)
            print(f"🎯 工具匹配度: {expected_found}/{len(scenario['expected_tools'])}")
        else:
            print(f"❌ 规划失败: {result['error']}")


async def demo_plan_validation():
    """演示计划验证功能"""
    print("\n" + "="*60)
    print("🔍 演示4: 计划验证功能")
    print("="*60)
    
    llm_client = MockLLMClient()
    agent = PlannerAgent(llm_client)
    await agent.initialize()
    
    # 测试有效计划
    valid_plan = {
        "plan_id": "test-plan-valid",
        "task_id": "test-task-valid",
        "steps": [
            {
                "step_id": 1,
                "name": "第一步",
                "description": "执行第一个步骤",
                "tool_name": "tool1",
                "tool_parameters": {},
                "dependencies": []
            },
            {
                "step_id": 2,
                "name": "第二步",
                "description": "执行第二个步骤",
                "tool_name": "tool2",
                "tool_parameters": {"input": "@{steps.1.result}"},
                "dependencies": [1]
            }
        ]
    }
    
    print("🧪 测试有效计划...")
    validation_result = await agent.validate_plan(valid_plan)
    print(f"结果: {'✅ 有效' if validation_result['valid'] else '❌ 无效'}")
    if validation_result['valid']:
        print(f"计划ID: {validation_result['plan_id']}")
        print(f"步骤数: {validation_result['steps_count']}")
    
    # 测试无效计划（循环依赖）
    invalid_plan = {
        "plan_id": "test-plan-invalid",
        "task_id": "test-task-invalid",
        "steps": [
            {
                "step_id": 1,
                "name": "第一步",
                "description": "执行第一个步骤",
                "tool_name": "tool1",
                "tool_parameters": {},
                "dependencies": [2]  # 依赖未来步骤
            },
            {
                "step_id": 2,
                "name": "第二步",
                "description": "执行第二个步骤",
                "tool_name": "tool2",
                "tool_parameters": {},
                "dependencies": []
            }
        ]
    }
    
    print("\n🧪 测试无效计划（未来依赖）...")
    validation_result = await agent.validate_plan(invalid_plan)
    print(f"结果: {'✅ 有效' if validation_result['valid'] else '❌ 无效'}")
    if not validation_result['valid']:
        print(f"错误: {validation_result['error']}")


async def main():
    """主演示函数"""
    print("🚀 MANDAS V1.3 TaskPlanner 集成演示")
    print("="*60)
    print("本演示展示TaskPlanner模块的核心功能和集成方式")
    
    try:
        # 运行各个演示
        await demo_task_planner_basic()
        await demo_planner_agent()
        await demo_complex_scenarios()
        await demo_plan_validation()
        
        print("\n" + "="*60)
        print("🎉 所有演示完成!")
        print("="*60)
        print("\n📋 TaskPlanner V1.3 主要特性:")
        print("  ✅ 智能任务分解和规划")
        print("  ✅ 依赖关系管理和验证")
        print("  ✅ 循环依赖检测")
        print("  ✅ 结构化JSON输出")
        print("  ✅ 与现有工具系统集成")
        print("  ✅ 重试机制和错误处理")
        print("  ✅ 计划优化支持")
        print("  ✅ 全面的日志记录")
        
        print("\n🔗 集成要点:")
        print("  - TaskPlanner: 核心规划引擎")
        print("  - PlannerAgent: 代理层封装")
        print("  - 与ToolRegistry无缝集成")
        print("  - 支持LLM Router选择")
        print("  - 兼容现有Memory Manager")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
