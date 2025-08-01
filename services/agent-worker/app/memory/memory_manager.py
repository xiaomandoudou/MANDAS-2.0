import asyncio
import json
import time
import random
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
        self._locks = {}  # 为每个key维护锁
    
    async def add_message(self, key: str, message: Dict[str, Any], ttl: Optional[int] = None):
        try:
            redis_key = f"user:{key}:history" if not key.startswith("user:") else f"{key}:history"
            full_key = f"memory:short:{redis_key}"
            
            if full_key not in self._locks:
                self._locks[full_key] = asyncio.Lock()
            
            async with self._locks[full_key]:
                async with self.redis_client.pipeline(transaction=True) as pipe:
                    score = time.time() * 1000000000 + random.randint(0, 999999)
                    value = json.dumps(message, ensure_ascii=False)
                    
                    pipe.zadd(full_key, {value: score})
                    
                    ttl_seconds = ttl if ttl else 300
                    pipe.expire(full_key, ttl_seconds)
                    
                    pipe.zremrangebyrank(full_key, 0, -51)
                    
                    await pipe.execute()
            
        except Exception as e:
            logger.error(f"Error adding message to short-term memory: {e}")
            raise
    
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
        self._context_cache = {}
        self._cache_ttl = 60
    
    async def initialize(self):
        """Initialize memory manager with Redis and ChromaDB connections"""
        try:
            self.redis_client = redis.from_url(settings.redis_url)
            
            try:
                self.chroma_client = chromadb.HttpClient(
                    host=settings.chromadb_url.replace("http://", "").split(":")[0],
                    port=int(settings.chromadb_url.split(":")[-1])
                )
                
                self.collection = self.chroma_client.get_or_create_collection(
                    name="mandas_memory",
                    metadata={"description": "Mandas Agent System Memory Store"}
                )
                logger.info("ChromaDB connection established successfully")
                
            except Exception as e:
                logger.warning(f"ChromaDB initialization failed: {e}, using Redis-only memory mode")
                self.chroma_client = None
                self.collection = None
            
            if self.collection is not None:
                try:
                    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                except Exception as e:
                    logger.warning(f"Embedding model initialization failed: {e}, disabling long-term memory")
                    self.collection = None
                    self.embedding_model = None
            else:
                self.embedding_model = None
            
            self.short_term_memory = ShortTermMemory(self.redis_client)
            
            if self.collection is not None and self.embedding_model is not None:
                self.long_term_memory = LongTermMemory(
                    self.chroma_client, self.collection, self.embedding_model
                )
                logger.info("Long-term memory (ChromaDB) enabled")
            else:
                logger.warning("Long-term memory disabled, using Redis-only memory mode")
                self.long_term_memory = None
            
            logger.info("Enhanced Memory Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced Memory Manager: {e}")
            logger.warning("Continuing with minimal memory functionality")
            self.redis_client = None
            self.chroma_client = None
            self.collection = None
            self.embedding_model = None
            self.short_term_memory = None
            self.long_term_memory = None
    
    async def _acquire_lock(self, lock_key: str, timeout: int = 5) -> bool:
        """Acquire distributed lock using Redis SETNX"""
        try:
            import time
            start_time = time.time()
            while time.time() - start_time < timeout:
                if await self.redis_client.set(lock_key, "locked", nx=True, ex=5):
                    return True
                await asyncio.sleep(0.1)
            return False
        except Exception as e:
            logger.error(f"Failed to acquire lock {lock_key}: {e}")
            return False
    
    async def _release_lock(self, lock_key: str) -> bool:
        """Release distributed lock"""
        try:
            await self.redis_client.delete(lock_key)
            return True
        except Exception as e:
            logger.error(f"Failed to release lock {lock_key}: {e}")
            return False
    
    async def acquire_lock(self, lock_key: str, timeout: int = 5) -> bool:
        """获取Redis分布式锁"""
        try:
            end_time = time.time() + timeout
            while time.time() < end_time:
                if await self.redis_client.set(lock_key, "locked", nx=True, ex=5):
                    return True
                await asyncio.sleep(0.1)
            return False
        except Exception as e:
            logger.error(f"Error acquiring lock {lock_key}: {e}")
            return False
    
    async def release_lock(self, lock_key: str):
        """释放Redis分布式锁"""
        try:
            await self.redis_client.delete(lock_key)
        except Exception as e:
            logger.error(f"Error releasing lock {lock_key}: {e}")

    async def get_context_for_llm(self, query: str, task_id: str) -> str:
        try:
            lock_key = f"lock:context:{task_id}"
            if not await self.acquire_lock(lock_key):
                logger.warning(f"Failed to acquire lock for context {task_id}")
                return "系统繁忙，请稍后重试。"
            
            try:
                cache_key = f"context:{task_id}:{hash(query)}"
                cached_context = await self.redis_client.get(cache_key)
                if cached_context:
                    return json.loads(cached_context)
                
                short_history = await self.short_term_memory.get_history(task_id, limit=5)
                await asyncio.sleep(0.01)  # 小延迟确保操作顺序
                
                knowledge = await self.long_term_memory.query_knowledge(query, limit=3) if self.long_term_memory else []
                
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
                    result = "暂无相关历史记录和知识库内容。"
                else:
                    result = "\n".join(context_parts)
                
                await self.redis_client.set(cache_key, json.dumps(result), ex=self._cache_ttl)
                
                return result
                
            finally:
                await self.release_lock(lock_key)
            
        except Exception as e:
            logger.error(f"Error getting context for LLM: {e}")
            return "获取上下文时出现错误。"
    
    async def remember(self, task_id: str, message: Dict[str, Any], short_term: bool = True, long_term: bool = False, ttl: Optional[int] = None):
        try:
            tasks = []
            if short_term:
                tasks.append(self.short_term_memory.add_message(task_id, message, ttl))
            
            if long_term and self.long_term_memory:
                tasks.append(self.long_term_memory.add_message(task_id, message, ttl))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        except Exception as e:
            logger.error(f"Error in remember: {e}")
            raise
    
    async def store_conversation(self, task_id: str, conversation: List[Dict[str, Any]]):
        try:
            for msg in conversation:
                await self.short_term_memory.add_message(task_id, msg)
            
            important_messages = [
                msg for msg in conversation 
                if len(msg.get("content", "")) > 100 or msg.get("name") == "Reviewer"
            ]
            
            if self.long_term_memory:
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
