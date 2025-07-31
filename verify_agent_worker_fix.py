#!/usr/bin/env python3
import subprocess
from datetime import datetime
import time

def verify_agent_worker_fix():
    print("=== Agent Worker Fix Verification ===")
    print(f"Timestamp: {datetime.now()}")
    
    print(f"\n🔍 Testing setup_logging import:")
    try:
        result = subprocess.run(
            ["docker", "exec", "mandas-agent-worker", "python", "-c", 
             "from app.core.logging import setup_logging; print('✅ setup_logging import successful')"],
            capture_output=True, text=True, cwd="/home/ubuntu/repos/MANDAS-2.0"
        )
        if result.returncode == 0:
            print(f"  ✅ setup_logging import working")
            print(f"  Output: {result.stdout.strip()}")
        else:
            print(f"  ❌ setup_logging import failed")
            print(f"     Error: {result.stderr.strip()}")
    except Exception as e:
        print(f"  ❌ Import test failed: {e}")
    
    print(f"\n🔍 Testing TaskConsumer import:")
    try:
        result = subprocess.run(
            ["docker", "exec", "mandas-agent-worker", "python", "-c", 
             "from app.worker.task_consumer import TaskConsumer; print('✅ TaskConsumer import successful')"],
            capture_output=True, text=True, cwd="/home/ubuntu/repos/MANDAS-2.0"
        )
        if result.returncode == 0:
            print(f"  ✅ TaskConsumer import working")
        else:
            print(f"  ❌ TaskConsumer import failed")
            print(f"     Error: {result.stderr.strip()}")
    except Exception as e:
        print(f"  ❌ TaskConsumer test failed: {e}")
    
    print(f"\n📋 Checking recent agent-worker logs:")
    try:
        result = subprocess.run(
            ["docker", "compose", "logs", "--tail=15", "agent-worker"],
            capture_output=True, text=True, cwd="/home/ubuntu/repos/MANDAS-2.0"
        )
        print(f"  Recent logs:")
        for line in result.stdout.strip().split('\n')[-10:]:
            if line.strip():
                print(f"    {line}")
    except Exception as e:
        print(f"  ❌ Log check failed: {e}")
    
    print(f"\n🔄 Container status:")
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "agent-worker"],
            capture_output=True, text=True, cwd="/home/ubuntu/repos/MANDAS-2.0"
        )
        print(f"  {result.stdout}")
    except Exception as e:
        print(f"  ❌ Status check failed: {e}")

if __name__ == "__main__":
    verify_agent_worker_fix()
