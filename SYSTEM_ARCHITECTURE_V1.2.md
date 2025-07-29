# MANDAS V1.2 System Architecture

## Overview
MANDAS V1.2 introduces BaseAgent and BaseTool abstractions for improved modularity and maintainability while maintaining external API compatibility.

## Architecture Changes

### Core Abstractions

#### BaseAgent
- Abstract base class for all agents
- Standardized interface: `initialize()`, `process_task()`, `get_capabilities()`, `health_check()`
- Supports dependency injection and configuration

#### BaseTool  
- Abstract base class for all tools
- Standardized interface: `initialize()`, `execute()`, `validate_parameters()`, `get_parameter_schema()`
- Built-in security validation and execution tracking

#### Enhanced Logging
- Trace ID propagation across all components
- Structured JSON logging with context
- Agent and tool execution tracking

### Component Integration

```
TaskConsumer (V1.2)
├── DefaultAgent (NEW)
│   ├── ToolRegistry (Enhanced)
│   │   ├── FileReaderTool (NEW)
│   │   ├── CodeRunnerTool (NEW)
│   │   └── BaseTool implementations
│   ├── MemoryManager (Existing)
│   └── EnhancedLogger (NEW)
├── GroupChatManager (Existing)
└── LLMRouterAgent (Existing)
```

### Execution Flow

1. **Task Reception**: TaskConsumer receives task from Redis stream
2. **Routing Decision**: LLMRouterAgent determines complexity
3. **Agent Selection**: 
   - Simple tasks → DefaultAgent
   - Complex tasks → GroupChatManager
4. **Tool Execution**: BaseTool implementations via ToolRegistry
5. **Logging**: EnhancedLogger with trace_id throughout
6. **Memory Storage**: Results stored via MemoryManager

### Backward Compatibility

- External API endpoints unchanged
- Legacy AgentManager and ToolExecutor maintained
- Gradual migration path for existing functionality

## Benefits

- **Modularity**: Clear separation of concerns with abstractions
- **Extensibility**: Easy to add new agents and tools
- **Observability**: Enhanced logging with trace correlation
- **Maintainability**: Standardized interfaces and patterns
- **Hot-pluggable**: Dynamic tool loading and registration

## V1.2 Implementation Details

### New Components
- `BaseAgent` - Abstract agent interface
- `BaseTool` - Abstract tool interface with security validation
- `DefaultAgent` - Simple task processing with automatic tool selection
- `EnhancedLogger` - Trace-aware structured logging
- `FileReaderTool` - File reading implementation inheriting BaseTool
- `CodeRunnerTool` - Code execution implementation inheriting BaseTool

### Enhanced Components
- `ToolRegistry` - Now supports BaseTool instance management and execution
- `TaskConsumer` - Integrated with EnhancedLogger and DefaultAgent routing

### Integration Points
- TaskConsumer routes simple tasks to DefaultAgent, complex to GroupChatManager
- ToolRegistry bridges YAML configs with BaseTool implementations
- EnhancedLogger provides trace context throughout execution flow
- DefaultAgent uses automatic tool selection based on prompt analysis

## Migration Strategy

1. **Phase 1**: Deploy V1.2 with backward compatibility
2. **Phase 2**: Gradually migrate complex workflows to new abstractions
3. **Phase 3**: Deprecate legacy components after validation
4. **Phase 4**: Full V1.2 architecture adoption

## Testing Strategy

- Existing V0.6/V1.1 test suites ensure no regressions
- New V1.2-specific tests validate abstractions and integrations
- End-to-end testing with both DefaultAgent and GroupChatManager workflows
- Performance benchmarking to ensure no degradation

## Future Roadmap (V1.3)

- Intelligent Agent orchestration mechanisms
- Advanced tool composition and chaining
- Dynamic agent selection based on task complexity
- Enhanced observability and monitoring capabilities
