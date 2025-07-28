import httpx
from typing import Dict, Any, List, Optional
from loguru import logger

from app.core.config import settings


class LLMRouter:
    def __init__(self):
        self.ollama_client = None
        self.available_models = []

    async def initialize(self):
        self.ollama_client = httpx.AsyncClient(
            base_url=settings.ollama_url,
            timeout=30.0  # Increase timeout for complex prompts
        )
        await self.discover_models()
        logger.info("LLM Router initialized successfully")

    async def discover_models(self):
        try:
            response = await self.ollama_client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                self.available_models = [model["name"] for model in data.get("models", [])]
                logger.info(f"Discovered Ollama models: {self.available_models}")
            else:
                logger.warning("Failed to discover Ollama models, using defaults")
                self.available_models = ["phi3:mini"]
        except Exception as e:
            logger.error(f"Error discovering models: {e}")
            self.available_models = ["phi3:mini"]

    async def get_default_config(self) -> Dict[str, Any]:
        model = self.available_models[0] if self.available_models else "phi3:mini"
        
        return {
            "config_list": [
                {
                    "model": model,
                    "base_url": f"{settings.ollama_url}/v1",
                    "api_key": "ollama",
                    "api_type": "openai"
                }
            ],
            "temperature": 0.7,
            "timeout": 300,
        }

    async def select_model(self, task_type: str, complexity: str = "medium") -> str:
        if not self.available_models:
            return "phi3:mini"
        
        if task_type in ["coding", "analysis"] and len(self.available_models) > 1:
            for model in self.available_models:
                if "code" in model.lower() or "coder" in model.lower():
                    return model
        
        if complexity == "high" and len(self.available_models) > 1:
            larger_models = [m for m in self.available_models if "70b" in m or "34b" in m]
            if larger_models:
                return larger_models[0]
        
        return self.available_models[0]

    async def generate_completion(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> str:
        if not model:
            model = await self.select_model("general")
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            logger.debug(f"Sending request to Ollama: {payload}")
            response = await self.ollama_client.post("/api/generate", json=payload)
            logger.debug(f"Ollama response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Ollama response data: {data}")
                return data.get("response", "")
            else:
                logger.error(f"LLM generation failed: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return "抱歉，生成回复时出现错误。"
                
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception args: {e.args}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return "抱歉，生成回复时出现错误。"

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> str:
        if not model:
            model = await self.select_model("chat")
        
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            logger.debug(f"Sending chat request to Ollama: {payload}")
            response = await self.ollama_client.post("/api/chat", json=payload)
            logger.debug(f"Ollama chat response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Ollama chat response data: {data}")
                return data.get("message", {}).get("content", "")
            else:
                logger.error(f"LLM chat completion failed: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return "抱歉，生成回复时出现错误。"
                
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception args: {e.args}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return "抱歉，生成回复时出现错误。"
