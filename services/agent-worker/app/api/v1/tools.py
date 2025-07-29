from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
from loguru import logger

from app.core.tools.tool_registry import ToolRegistry

router = APIRouter()

@router.get("/")
async def list_tools():
    try:
        tool_registry = ToolRegistry("/app/tools.d")
        await tool_registry.initialize()
        
        tools = tool_registry.list_tools(enabled_only=False)
        
        tools_data = []
        for tool in tools:
            tools_data.append({
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "version": tool.version,
                "author": tool.author,
                "enabled": tool.enabled,
                "parameters": tool.parameters,
                "required_permissions": tool.required_permissions
            })
        
        return {
            "total": len(tools_data),
            "tools": tools_data
        }
        
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tools"
        )
