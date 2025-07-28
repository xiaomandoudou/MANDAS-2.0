from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.auth import get_current_user
from loguru import logger

router = APIRouter()


class ToolResponse(BaseModel):
    name: str
    description: str
    category: str
    version: str
    author: str
    enabled: bool
    parameters: Dict[str, Any]
    required_permissions: List[str]


class ToolsListResponse(BaseModel):
    tools: List[ToolResponse]
    total_count: int
    enabled_count: int
    categories: Dict[str, int]


@router.get("/", response_model=ToolsListResponse)
async def list_tools(
    category: Optional[str] = None,
    enabled_only: bool = True,
    current_user: dict = Depends(get_current_user)
):
    try:
        mock_tools = [
            {
                "name": "echo",
                "description": "简单的回显工具",
                "category": "utility",
                "version": "1.0.0",
                "author": "MANDAS System",
                "enabled": True,
                "parameters": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"]
                },
                "required_permissions": []
            },
            {
                "name": "python_executor",
                "description": "在安全沙箱中执行Python代码",
                "category": "code_execution",
                "version": "1.0.0",
                "author": "MANDAS System",
                "enabled": True,
                "parameters": {
                    "type": "object",
                    "properties": {"code": {"type": "string"}},
                    "required": ["code"]
                },
                "required_permissions": ["code_execution"]
            },
            {
                "name": "shell_executor",
                "description": "在安全沙箱中执行Shell命令",
                "category": "system",
                "version": "1.0.0",
                "author": "MANDAS System",
                "enabled": True,
                "parameters": {
                    "type": "object",
                    "properties": {"command": {"type": "string"}},
                    "required": ["command"]
                },
                "required_permissions": ["system_access", "shell_execution"]
            }
        ]
        
        filtered_tools = mock_tools
        if category:
            filtered_tools = [t for t in filtered_tools if t["category"] == category]
        if enabled_only:
            filtered_tools = [t for t in filtered_tools if t["enabled"]]
        
        categories = {}
        for tool in filtered_tools:
            cat = tool["category"]
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "tools": filtered_tools,
            "total_count": len(mock_tools),
            "enabled_count": len([t for t in mock_tools if t["enabled"]]),
            "categories": categories
        }
        
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tools"
        )
