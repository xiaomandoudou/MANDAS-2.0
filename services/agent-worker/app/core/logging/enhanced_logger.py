import uuid
import time
import json
from typing import Dict, Any, Optional
from loguru import logger
from contextlib import contextmanager


class EnhancedLogger:
    """Enhanced logger with trace_id support and structured logging"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.current_trace_id: Optional[str] = None
        self.current_task_id: Optional[str] = None
    
    def set_trace_context(self, trace_id: str, task_id: Optional[str] = None):
        """Set trace context for current execution"""
        self.current_trace_id = trace_id
        self.current_task_id = task_id
    
    def generate_trace_id(self) -> str:
        """Generate new trace ID"""
        return str(uuid.uuid4())
    
    @contextmanager
    def trace_context(self, trace_id: Optional[str] = None, task_id: Optional[str] = None):
        """Context manager for trace logging"""
        old_trace_id = self.current_trace_id
        old_task_id = self.current_task_id
        
        self.current_trace_id = trace_id or self.generate_trace_id()
        self.current_task_id = task_id
        
        try:
            yield self.current_trace_id
        finally:
            self.current_trace_id = old_trace_id
            self.current_task_id = old_task_id
    
    def _get_extra_context(self, **kwargs) -> Dict[str, Any]:
        """Get extra context for logging"""
        extra = {
            "trace_id": self.current_trace_id or "",
            "task_id": self.current_task_id or "",
            "component": self.component_name,
            "timestamp": time.time()
        }
        extra.update(kwargs)
        return extra
    
    def info(self, message: str, **kwargs):
        """Log info message with trace context"""
        logger.bind(**self._get_extra_context(**kwargs)).info(message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with trace context"""
        logger.bind(**self._get_extra_context(**kwargs)).debug(message)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with trace context"""
        logger.bind(**self._get_extra_context(**kwargs)).warning(message)
    
    def error(self, message: str, **kwargs):
        """Log error message with trace context"""
        logger.bind(**self._get_extra_context(**kwargs)).error(message)
    
    def log_tool_execution(self, tool_name: str, parameters: Dict[str, Any], result: Dict[str, Any]):
        """Log tool execution with structured data"""
        self.info(
            f"Tool execution: {tool_name}",
            tool_name=tool_name,
            parameters_hash=hash(str(parameters)),
            success=result.get("success", False),
            execution_time=result.get("execution_time", 0)
        )
    
    def log_agent_action(self, agent_name: str, action: str, details: Dict[str, Any]):
        """Log agent action with structured data"""
        self.info(
            f"Agent action: {agent_name} - {action}",
            agent_name=agent_name,
            action=action,
            details=details
        )
    
    def log_task_transition(self, task_id: str, from_status: str, to_status: str):
        """Log task status transition"""
        self.info(
            f"Task transition: {task_id} {from_status} -> {to_status}",
            task_id=task_id,
            from_status=from_status,
            to_status=to_status,
            transition_type="status_change"
        )
