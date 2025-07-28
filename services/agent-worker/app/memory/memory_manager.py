import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import chromadb
import redis.asyncio as redis
from sentence_transformers import SentenceTransformer
from loguru import logger

from app.core.config import settings


class BaseMemory(ABC):
    
    @abstractmethod
    async def add_message(self, key: str, message: Dict[str, Any], ttl: Optional[int] = None):
        pass
    
    @abstractmethod
    async def get_history(self, key: str, limit: int = 10) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def query_knowledge(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        pass


class ShortTermMemory(BaseMemory):
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.default_ttl = 3600  # 1小时
    
    async def add_message(self, key: str, message: Dict[str, Any], ttl: Optional[int] = None):
        try:
            score = time.time()
            value = json.dumps(message, ensure_ascii=False)
            
            redis_key = f"user:{key}:history" if not key.startswith("user:") else f"{key}:history"
            
            await self.redis_client.zadd(f"memory:short:{redis_key}", {value: score})
            
            ttl_seconds = ttl if ttl else 300  # 5分钟
            await self.redis_client.expire(f"memory:short:{redis_key}", ttl_seconds)
            
            await self.redis_client.zremrangebyrank(f"memory:short:{redis_key}", 0, -51)
            
        except Exception as e:
            logger.error(f"Error adding message to short-term memory: {e}")
    
    async def get_history(self, key: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            redis_key = f"user:{key}:history" if not key.startswith("user:") else f"{key}:history"
            
            messages = await self.redis_client.zrevrange(
                f"memory:short:{redis_key}", 0, limit - 1, withscores=False
            )
            
            result = []
            for msg in messages:
                try:
                    result.append(json.loads(msg))
                except json.JSONDecodeError:
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting short-term memory history: {e}")
            return []
    
    async def query_knowledge(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        return []


class LongTermMemory(BaseMemory):
    
    def __init__(self, chroma_client, collection, embedding_model):
        self.chroma_client = chroma_client
        self.collection = collection
        self.embedding_model = embedding_model
    
    async def add_message(self, key: str, message: Dict[str, Any], ttl: Optional[int] = None):
        try:
            content = message.get("content", "")
            if len(content) < 50:  # 只存储有意义的长内容
                return
            
            embedding = self.embedding_model.encode([content])[0].tolist()
            
            doc_id = f"{key}_{int(time.time())}"
            self.collection.add(
                documents=[content],
                embeddings=[embedding],
                metadatas=[{
                    "key": key,
                    "type": "conversation",
                    "timestamp": time.time(),
                    **message
                }],
                ids=[doc_id]
            )
            
        except Exception as e:
            logger.error(f"Error adding message to long-term memory: {e}")
    
    async def get_history(self, key: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            results = self.collection.query(
                where={"key": key, "type": "conversation"},
                n_results=limit
            )
            
            if not results["documents"] or not results["documents"][0]:
                return []
            
            history = []
            for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
                history.append({
                    "content": doc,
                    "timestamp": metadata.get("timestamp", 0),
                    "role": metadata.get("role", "unknown"),
                    "name": metadata.get("name", "unknown")
                })
            
            history.sort(key=lambda x: x["timestamp"], reverse=True)
            return history
            
        except Exception as e:
            logger.error(f"Error getting long-term memory history: {e}")
            return []
    
    async def query_knowledge(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        try:
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where={"type": {"$in": ["document", "knowledge"]}}
            )
            
            if not results["documents"] or not results["documents"][0]:
                return []
            
            knowledge = []
            for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
                knowledge.append({
                    "content": doc[:500] + "..." if len(doc) > 500 else doc,
                    "source": metadata.get("source", "unknown"),
                    "type": metadata.get("type", "knowledge"),
                    "relevance_score": metadata.get("distance", 0)
                })
            
            return knowledge
            
        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return []


class MemoryManager:
    
    def __init__(self):
        self.redis_client = None
        self.chroma_client = None
        self.collection = None
        self.embedding_model = None
        self.short_term_memory = None
        self.long_term_memory = None
    
    async def initialize(self):
        try:
            self.redis_client = redis.from_url(settings.redis_url)
            
            self.chroma_client = chromadb.HttpClient(
                host=settings.chromadb_url.replace("http://", "").split(":")[0],
                port=int(settings.chromadb_url.split(":")[-1])
            )
            
            self.collection = self.chroma_client.get_or_create_collection(
                name="mandas_memory",
                metadata={"description": "Mandas Agent System Memory Store"}
            )
            
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            self.short_term_memory = ShortTermMemory(self.redis_client)
            self.long_term_memory = LongTermMemory(
                self.chroma_client, self.collection, self.embedding_model
            )
            
            logger.info("Enhanced Memory Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced Memory Manager: {e}")
            raise
    
    async def get_context_for_llm(self, query: str, task_id: str) -> str:
        try:
            short_history = await self.short_term_memory.get_history(task_id, limit=5)
            
            knowledge = await self.long_term_memory.query_knowledge(query, limit=3)
            
            context_parts = []
            
            if short_history:
                context_parts.append("**最近对话历史**:")
                for msg in short_history:
                    name = msg.get("name", "unknown")
                    content = msg.get("content", "")[:200]
                    context_parts.append(f"- {name}: {content}")
            
            if knowledge:
                context_parts.append("\n**相关知识库内容**:")
                for item in knowledge:
                    source = item.get("source", "unknown")
                    content = item.get("content", "")
                    context_parts.append(f"- [{source}]: {content}")
            
            if not context_parts:
                return "暂无相关历史记录和知识库内容。"
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting context for LLM: {e}")
            return "获取上下文时出现错误。"
    
    async def remember(self, task_id: str, message: Dict[str, Any], short_term: bool = True, long_term: bool = False, ttl: Optional[int] = None):
        try:
            if short_term:
                await self.short_term_memory.add_message(task_id, message, ttl)
            
            if long_term:
                await self.long_term_memory.add_message(task_id, message, ttl)
                
        except Exception as e:
            logger.error(f"Error in remember: {e}")
    
    async def store_conversation(self, task_id: str, conversation: List[Dict[str, Any]]):
        try:
            for msg in conversation:
                await self.short_term_memory.add_message(task_id, msg)
            
            important_messages = [
                msg for msg in conversation 
                if len(msg.get("content", "")) > 100 or msg.get("name") == "Reviewer"
            ]
            
            for msg in important_messages:
                await self.long_term_memory.add_message(task_id, msg)
            
            logger.info(f"Stored conversation for task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to store conversation for task {task_id}: {e}")
    
    async def get_relevant_context(self, query: str, max_results: int = 3) -> str:
        return await self.get_context_for_llm(query, "general")
    
    async def get_context(self, user_id: str, task_id: str) -> str:
        """用户建议的接口：自动拼接对话历史与知识检索内容"""
        return await self.get_context_for_llm(f"user:{user_id}", task_id)
    
    def format_conversation(self, conversation: List[Dict[str, Any]]) -> str:
        formatted_parts = []
        for msg in conversation:
            role = msg.get("role", "unknown")
            name = msg.get("name", "unknown")
            content = msg.get("content", "")
            formatted_parts.append(f"{name} ({role}): {content}")
        
        return "\n".join(formatted_parts)
