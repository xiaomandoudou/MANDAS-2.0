#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/ubuntu/repos/MANDAS-2.0/services/agent-worker')

def test_taskplanner_import():
    """Test TaskPlanner module imports"""
    try:
        from app.core.planning import TaskPlanner, PlanStep, TaskPlan
        print("✅ TaskPlanner imports successful")
        print("✅ PlanStep dataclass available")
        print("✅ TaskPlan dataclass available")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

def test_taskplanner_instantiation():
    """Test TaskPlanner class instantiation"""
    try:
        from app.core.planning import TaskPlanner
        from app.llm.llm_router import LLMRouter
        
        class MockLLMRouter:
            async def route_request(self, request):
                return {
                    "choices": [{
                        "message": {
                            "content": '{"summary": "测试计划", "steps": []}'
                        }
                    }]
                }
        
        mock_router = MockLLMRouter()
        planner = TaskPlanner(mock_router)
        print("✅ TaskPlanner instantiation successful")
        return True
    except Exception as e:
        print(f"❌ TaskPlanner instantiation failed: {e}")
        return False

if __name__ == "__main__":
    print("=== TaskPlanner Module Testing ===")
    
    import_success = test_taskplanner_import()
    if import_success:
        instantiation_success = test_taskplanner_instantiation()
    else:
        instantiation_success = False
    
    if import_success and instantiation_success:
        print("\n✅ All TaskPlanner tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some TaskPlanner tests failed!")
        sys.exit(1)
