#!/usr/bin/env python3

import sys
import os
import asyncio
sys.path.append('/home/ubuntu/repos/MANDAS-2.0/services/api-gateway')

def test_api_endpoint_imports():
    """Test that V1.3 API endpoints can be imported"""
    try:
        from app.api.v1.tasks import get_task_plan, regenerate_task_plan, update_plan_step
        print("✅ V1.3 API endpoints import successfully")
        print("  - get_task_plan function available")
        print("  - regenerate_task_plan function available") 
        print("  - update_plan_step function available")
        return True
    except ImportError as e:
        print(f"❌ API endpoint import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error importing API endpoints: {e}")
        return False

def test_api_endpoint_signatures():
    """Test API endpoint function signatures"""
    try:
        from app.api.v1.tasks import get_task_plan, regenerate_task_plan, update_plan_step
        import inspect
        
        sig = inspect.signature(get_task_plan)
        params = list(sig.parameters.keys())
        if 'task_id' in params and 'include_result' in params:
            print("✅ get_task_plan has correct parameters (task_id, include_result)")
        else:
            print(f"❌ get_task_plan missing expected parameters: {params}")
            
        sig = inspect.signature(regenerate_task_plan)
        params = list(sig.parameters.keys())
        if 'task_id' in params:
            print("✅ regenerate_task_plan has correct parameters (task_id)")
        else:
            print(f"❌ regenerate_task_plan missing expected parameters: {params}")
            
        sig = inspect.signature(update_plan_step)
        params = list(sig.parameters.keys())
        if 'task_id' in params and 'step_id' in params and 'step_data' in params:
            print("✅ update_plan_step has correct parameters (task_id, step_id, step_data)")
        else:
            print(f"❌ update_plan_step missing expected parameters: {params}")
            
        return True
    except Exception as e:
        print(f"❌ Error checking API signatures: {e}")
        return False

if __name__ == "__main__":
    print("=== V1.3 API Endpoint Testing ===")
    
    import_success = test_api_endpoint_imports()
    if import_success:
        signature_success = test_api_endpoint_signatures()
    else:
        signature_success = False
    
    if import_success and signature_success:
        print("\n✅ All V1.3 API endpoint tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some V1.3 API endpoint tests failed!")
        sys.exit(1)
