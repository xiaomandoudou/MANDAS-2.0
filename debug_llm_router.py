#!/usr/bin/env python3
"""Debug LLM Router Communication Issue"""

import asyncio
import sys
import os
import httpx
import json

sys.path.append('/home/ubuntu/repos/MANDAS-2.0/services/agent-worker')

from app.llm.llm_router import LLMRouter
from app.core.config import settings


async def test_direct_httpx():
    """Test direct httpx communication with Ollama"""
    print("🔍 Testing direct httpx communication with Ollama...")
    
    try:
        async with httpx.AsyncClient(base_url="http://localhost:11434") as client:
            response = await client.get("/api/tags")
            print(f"✅ Model discovery: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                print(f"   Available models: {models}")
            
            payload = {
                "model": "phi3:mini",
                "prompt": "Hello, respond with just 'Hi'",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 10
                }
            }
            
            response = await client.post("/api/generate", json=payload)
            print(f"✅ Generation test: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data.get('response', 'No response')}")
            else:
                print(f"   Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Direct httpx test failed: {e}")


async def test_llm_router():
    """Test LLM Router class"""
    print("\n🔍 Testing LLM Router class...")
    
    try:
        router = LLMRouter()
        await router.initialize()
        
        print(f"✅ Router initialized")
        print(f"   Available models: {router.available_models}")
        print(f"   Ollama URL: {settings.ollama_url}")
        
        response = await router.generate_completion(
            prompt="Hello, respond with just 'Hi'",
            model="phi3:mini",
            max_tokens=10,
            temperature=0.1
        )
        
        print(f"✅ Generation result: '{response}'")
        
        if not response or response == "抱歉，生成回复时出现错误。":
            print("❌ LLM Router generation failed")
            
            print("\n🔍 Debugging HTTP client...")
            print(f"   Base URL: {router.ollama_client.base_url}")
            print(f"   Client type: {type(router.ollama_client)}")
            
            try:
                payload = {
                    "model": "phi3:mini",
                    "prompt": "Hello",
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 10
                    }
                }
                
                response = await router.ollama_client.post("/api/generate", json=payload)
                print(f"   Raw response status: {response.status_code}")
                print(f"   Raw response text: {response.text[:200]}...")
                
            except Exception as e:
                print(f"   Raw request error: {e}")
                print(f"   Error type: {type(e)}")
        
    except Exception as e:
        print(f"❌ LLM Router test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_config():
    """Test configuration"""
    print("\n🔍 Testing configuration...")
    
    print(f"   OLLAMA_URL from settings: {settings.ollama_url}")
    print(f"   Environment OLLAMA_URL: {os.getenv('OLLAMA_URL', 'Not set')}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.ollama_url}/api/tags", timeout=5.0)
            print(f"   URL reachable: {response.status_code}")
    except Exception as e:
        print(f"   URL not reachable: {e}")


async def main():
    """Main diagnostic function"""
    print("🚀 Starting LLM Router Diagnostic...")
    
    await test_config()
    await test_direct_httpx()
    await test_llm_router()
    
    print("\n🎯 Diagnostic complete!")


if __name__ == "__main__":
    asyncio.run(main())
