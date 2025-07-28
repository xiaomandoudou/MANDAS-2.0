import chromadb
import httpx
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from loguru import logger

from app.core.config import settings


class MemoryManager:
    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.embedding_model = None

    async def initialize(self):
        try:
            self.chroma_client = chromadb.HttpClient(
                host=settings.chromadb_url.replace("http://", "").split(":")[0],
                port=int(settings.chromadb_url.split(":")[-1])
            )
            
            self.collection = self.chroma_client.get_or_create_collection(
                name="mandas_memory",
                metadata={"description": "Mandas Agent System Memory Store"}
            )
            
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info("Memory Manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Memory Manager: {e}")
            raise

    async def store_conversation(self, task_id: str, conversation: List[Dict[str, Any]]):
        try:
            conversation_text = self.format_conversation(conversation)
            
            embedding = self.embedding_model.encode([conversation_text])[0].tolist()
            
            self.collection.add(
                documents=[conversation_text],
                embeddings=[embedding],
                metadatas=[{
                    "task_id": task_id,
                    "type": "conversation"
                }],
                ids=[f"task_{task_id}"]
            )
            
            logger.info(f"Stored conversation for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to store conversation for task {task_id}: {e}")

    async def get_relevant_context(self, query: str, max_results: int = 3) -> str:
        try:
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results
            )
            
            if not results["documents"] or not results["documents"][0]:
                return "暂无相关历史记录。"
            
            context_parts = []
            for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
                task_id = metadata.get("task_id", "unknown")
                context_parts.append(f"任务 {task_id}:\n{doc[:500]}...")
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Failed to get relevant context: {e}")
            return "获取历史记录时出现错误。"

    def format_conversation(self, conversation: List[Dict[str, Any]]) -> str:
        formatted_parts = []
        for msg in conversation:
            role = msg.get("role", "unknown")
            name = msg.get("name", "unknown")
            content = msg.get("content", "")
            formatted_parts.append(f"{name} ({role}): {content}")
        
        return "\n".join(formatted_parts)
