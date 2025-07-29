from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from pydantic import BaseModel

from app.core.auth import get_current_user
from loguru import logger

router = APIRouter()


class MemoryQueryRequest(BaseModel):
    query: str
    max_results: int = 3
    memory_type: str = "all"  # "short", "long", "all"


class MemoryQueryResponse(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    total_results: int


@router.post("/query", response_model=MemoryQueryResponse)
async def query_memory(
    request: MemoryQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        mock_results = [
            {
                "content": f"相关记忆内容: {request.query}",
                "source": "conversation",
                "timestamp": "2025-07-28T03:00:00Z",
                "relevance_score": 0.95,
                "type": "short_term"
            },
            {
                "content": f"知识库相关内容: {request.query}",
                "source": "knowledge_base",
                "timestamp": "2025-07-27T15:30:00Z",
                "relevance_score": 0.87,
                "type": "long_term"
            }
        ]
        
        if request.memory_type != "all":
            mock_results = [r for r in mock_results if r["type"] == request.memory_type]
        
        mock_results = mock_results[:request.max_results]
        
        return {
            "results": mock_results,
            "query": request.query,
            "total_results": len(mock_results)
        }
        
    except Exception as e:
        logger.error(f"Error querying memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query memory"
        )


@router.get("/context")
async def get_context(
    user_id: str,
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        mock_context = {
            "short_term_history": [
                {
                    "role": "user",
                    "content": "请帮我分析这个数据",
                    "timestamp": "2025-07-28T03:55:00Z"
                },
                {
                    "role": "assistant", 
                    "content": "我来帮您分析数据",
                    "timestamp": "2025-07-28T03:55:30Z"
                }
            ],
            "long_term_knowledge": [
                {
                    "content": "数据分析相关知识...",
                    "source": "knowledge_base",
                    "relevance_score": 0.92
                }
            ],
            "context_summary": f"用户 {user_id} 在任务 {task_id} 中的上下文信息"
        }
        
        return mock_context
        
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get context"
        )
