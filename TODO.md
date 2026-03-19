# AIBOTTO - New Features Implementation Plan

## Overview
Implementation plan for three major enhancements to the AIBOTTO AI agent system:
1. Token Count Tracking for Cost Estimations
2. Schedule Actions Tool for LLM Execution  
3. User Clarification Tool for Improved Task Accuracy

## Feature 1: Token Count Tracking for Cost Estimations

### Goal
Track API token usage across all LLM calls to provide cost estimates and optimize usage.

### Implementation Components

#### Core Services
- **Token Tracker Service** (`src/aibotto/services/token_tracker.py`)
  - Track input/output tokens per API call
  - Calculate costs based on model pricing
  - Store usage history in database

- **LLM Client Integration**
  - Modify `LLMClient.chat_completion()` to track tokens
  - Update response parsing to extract token counts
  - Log usage to database

- **Cost Reporting Tool**
  - Create `cost_estimator` tool for users
  - Show usage statistics and costs
  - Set budget alerts and limits

#### Database Schema
```sql
CREATE TABLE IF NOT EXISTS token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd DECIMAL(10, 6),
    model_used TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Configuration
```python
# Token tracking configuration
TOKEN_TRACKING_ENABLED: bool = EnvLoader.get_bool("TOKEN_TRACKING_ENABLED", True)
COST_MODEL: str = EnvLoader.get_str("COST_MODEL", "openai")
MAX_DAILY_BUDGET: float = EnvLoader.get_float("MAX_DAILY_BUDGET", 10.0)
```

#### TDD Implementation Plan
1. **RED:** Write failing test for token counting in LLM client
2. **GREEN:** Implement token tracking with mock API responses
3. **RED:** Write failing test for cost calculation
4. **GREEN:** Implement cost calculation with pricing models
5. **RED:** Write failing test for database storage
6. **GREEN:** Implement database integration
7. **RED:** Write failing test for cost reporting tool
8. **GREEN:** Implement cost reporting tool

## Feature 2: Schedule Actions Tool

### Goal
Allow users to schedule LLM actions to be executed at specific times.

### Implementation Components

#### Core Services
- **Scheduler Service** (`src/aibotto/services/scheduler.py`)
  - Use `apscheduler` for cron-based scheduling
  - Store scheduled tasks in database
  - Handle task execution and cleanup

- **Schedule Tool Executor**
  - Create `schedule_executor.py`
  - Validate schedule format (cron or datetime)
  - Store scheduled tasks with proper metadata
  - Provide confirmation and status tracking

- **Task Execution Handler**
  - Integrate with existing tool execution system
  - Handle scheduled task execution in context
  - Provide execution feedback to users

#### Database Schema
```sql
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    scheduled_time DATETIME NOT NULL,
    tool_name TEXT NOT NULL,
    arguments_json TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    executed_at DATETIME,
    result_content TEXT,
    error_message TEXT
);
```

#### Configuration
```python
# Scheduler configuration
SCHEDULER_TIMEZONE: str = EnvLoader.get_str("SCHEDULER_TIMEZONE", "UTC")
MAX_SCHEDULED_TASKS: int = EnvLoader.get_int("MAX_SCHEDULED_TASKS", 100)
```

#### TDD Implementation Plan
1. **RED:** Write failing test for schedule tool validation
2. **GREEN:** Implement basic schedule validation
3. **RED:** Write failing test for database storage
4. **GREEN:** Implement database integration for schedules
5. **RED:** Write failing test for scheduler service
6. **GREEN:** Implement scheduler with apscheduler
7. **RED:** Write failing test for task execution
8. **GREEN:** Implement task execution in context

## Feature 3: User Clarification Tool

### Goal
Allow LLM to ask clarifying questions before proceeding with complex tasks.

### Implementation Components

#### Core Services
- **Clarification Service** (`src/aibotto/services/clarification.py`)
  - Manage question-asking workflow
  - Track pending questions and answers
  - Maintain conversation context

- **Clarification Tool Executor**
  - Create `clarification_executor.py`
  - Generate appropriate clarifying questions
  - Store questions and capture user responses
  - Resume task execution with clarified context

- **Question Generation Logic**
  - Analyze task requirements for ambiguities
  - Generate targeted clarifying questions
  - Prioritize questions based on task complexity

#### Database Schema
```sql
CREATE TABLE IF NOT EXISTS clarifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type TEXT NOT NULL,
    context_json TEXT NOT NULL,
    answer_text TEXT,
    answered_at DATETIME,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Configuration
```python
# Clarification configuration
MAX_CLARIFICATION_ATTEMPTS: int = EnvLoader.get_int("MAX_CLARIFICATION_ATTEMPTS", 3)
CLARIFICATION_TIMEOUT: int = EnvLoader.get_int("CLARIFICATION_TIMEOUT", 300)  # 5 minutes
```

#### TDD Implementation Plan
1. **RED:** Write failing test for question generation
2. **GREEN:** Implement basic question generation
3. **RED:** Write failing test for clarification tool
4. **GREEN:** Implement clarification tool executor
5. **RED:** Write failing test for state management
6. **GREEN:** Implement conversation state tracking
7. **RED:** Write failing test for workflow integration
8. **GREEN:** Implement integration with existing tool calling

## Implementation Priority

### High Priority (Implementation Order)
1. **Token Count Tracking** - Foundation for cost optimization
2. **User Clarification Tool** - Improves task accuracy
3. **Schedule Actions Tool** - Adds automation capability

### Medium Priority
- Configuration updates
- Integration testing
- Documentation updates

### Low Priority
- User guides
- Documentation updates

## Risk Mitigation

### Technical Risks
1. **API Token Tracking**: Some APIs may not return token counts
   - **Mitigation**: Use estimated token counts as fallback
   - **Monitoring**: Log when estimated counts are used

2. **Scheduler Reliability**: External dependencies for scheduling
   - **Mitigation**: Implement retry logic and status tracking
   - **Monitoring**: Track scheduled task success/failure rates

3. **Clarification Overhead**: Too many questions may frustrate users
   - **Mitigation**: Implement smart question prioritization
   - **Limits**: Enforce maximum clarification attempts

### Security Considerations
- All new tools must follow existing security patterns
- Database schema changes require migration scripts
- User data protection for scheduled tasks and clarifications

## Testing Strategy

### Unit Tests
- Token tracking accuracy and cost calculations
- Schedule validation and cron parsing
- Question generation and clarification workflow
- Database operations for all new features

### Integration Tests
- End-to-end token tracking with real API calls
- Scheduled task execution in conversation context
- Clarification workflow integration with tool calling

### E2E Tests
- Complete cost estimation workflow
- Schedule task creation and execution
- Clarification question and answer cycle

## Dependencies

### External Dependencies
- `apscheduler` for scheduling functionality
- Potentially additional token counting libraries

### Internal Dependencies
- All features depend on existing database operations
- Token tracking depends on LLM API response parsing
- Schedule tool requires scheduler library integration
- Clarification tool requires conversation state management

## Success Metrics

### Technical Metrics
- All tests passing (target: 100%)
- API cost reduction through token optimization
- Successful scheduled task execution rate > 95%
- Clarification completion rate > 90%

### User Experience Metrics
- User satisfaction with cost visibility
- Task accuracy improvement through clarification
- Adoption rate of scheduling feature

## Rollout Plan

### Phase 1: Foundation (Week 1-2)
- Implement token tracking system
- Basic cost estimation tools
- Database schema updates

### Phase 2: Core Features (Week 3-4)
- User clarification tool
- Schedule actions tool
- Integration testing

### Phase 3: Polish & Documentation (Week 5-6)
- Performance optimization
- User documentation
- Final testing and bug fixes

## Monitoring & Maintenance

### Monitoring Requirements
- Track API token usage and costs
- Monitor scheduled task success/failure rates
- Track clarification question effectiveness
- Monitor database performance with new tables

### Maintenance Tasks
- Regular cost model updates
- Scheduler maintenance and optimization
- Clarification logic improvements
- Database performance monitoring

## Future Enhancements

### Potential Expansions
- Multi-model cost tracking
- Advanced scheduling features (recurring tasks, dependencies)
- Smart clarification with ML-based question prioritization
- Integration with external calendar systems
- Cost budget alerts and notifications

### Scalability Considerations
- Database indexing for new tables
- Caching for frequently accessed cost data
- Load balancing for scheduled task execution
- Queue system for clarification processing