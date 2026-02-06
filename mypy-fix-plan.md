# MyPy Type Checking Issues - Fix Plan

## Summary
- **Total Errors**: 42 MyPy errors across 10 files
- **Priority**: High (Type safety is crucial for maintainability)

## Error Categories

### 1. Missing Type Annotations (Easiest - 12 errors)
**Files**: Multiple
**Issue**: Functions missing return type annotations or parameter type annotations
**Fix**: Add `-> None` for void functions, proper parameter types

### 2. Generic Type Parameters (Medium - 3 errors)
**Files**: 
- `src/aibotto/ai/prompt_templates.py`
- `src/aibotto/db/operations.py`
- `src/aibotto/bot/handlers.py`
**Issue**: Missing type parameters for generic types like `dict`, `Callable`
**Fix**: Add proper type parameters (e.g., `dict[str, Any]`)

### 3. Union Attribute Access (Medium - 8 errors)
**Files**: `src/aibotto/bot/telegram_bot.py`
**Issue**: Accessing attributes on potentially None values
**Fix**: Add None checks or use proper union handling

### 4. Return Type Mismatches (Medium - 6 errors)
**Files**: 
- `src/aibotto/cli/security.py`
- `src/aibotto/cli/executor.py`
**Issue**: Functions returning wrong types
**Fix**: Update return types or fix function logic

### 5. OpenAI API Integration Issues (Hard - 8 errors)
**Files**: `src/aibotto/ai/llm_client.py`, `src/aibotto/ai/tool_calling.py`
**Issue**: Complex OpenAI API type issues
**Fix**: Requires proper typing of async responses and API calls

### 6. Database Model Issues (Medium - 3 errors)
**Files**: `src/aibotto/db/models.py`, `src/aibotto/db/operations.py`
**Issue**: Type issues in database operations
**Fix**: Proper typing of database models and operations

## Fix Implementation Plan

### Phase 1: Quick Wins (Missing Type Annotations)
**Priority**: High, Effort: Low
**Files**: 
- `src/aibotto/db/models.py`
- `src/aibotto/db/operations.py`
- `src/aibotto/cli/security.py`
- `src/aibotto/cli/executor.py`
- `src/aibotto/bot/telegram_bot.py`
- `src/aibotto/ai/llm_client.py`
- `src/aibotto/ai/tool_calling.py`
- `src/aibotto/utils/message_splitter.py`

**Tasks**:
1. Add `-> None` to void functions
2. Add missing parameter type annotations
3. Fix generic type parameters

### Phase 2: Union Handling and Return Types
**Priority**: High, Effort: Medium
**Files**: 
- `src/aibotto/bot/telegram_bot.py` (union attribute access)
- `src/aibotto/cli/security.py` (return type mismatches)
- `src/aibotto/cli/executor.py` (return type mismatches)

**Tasks**:
1. Add proper None checks for union types
2. Fix return type annotations
3. Update function signatures to match actual return types

### Phase 3: Database Layer Typing
**Priority**: Medium, Effort: Medium
**Files**: 
- `src/aibotto/db/models.py`
- `src/aibotto/db/operations.py`

**Tasks**:
1. Fix datetime assignment issues
2. Add proper type annotations for database operations
3. Type check database models

### Phase 4: OpenAI API Integration
**Priority**: Medium, Effort: High
**Files**: 
- `src/aibotto/ai/llm_client.py`
- `src/aibotto/ai/tool_calling.py`

**Tasks**:
1. Fix OpenAI API call overloads
2. Properly type async responses
3. Handle API response typing correctly

### Phase 5: Advanced Generic Types
**Priority**: Low, Effort: Medium
**Files**: 
- `src/aibotto/bot/handlers.py`
- `src/aibotto/ai/prompt_templates.py`

**Tasks**:
1. Fix generic type parameters
2. Add proper Callable type annotations

## Implementation Strategy

### Task 1: Fix Missing Type Annotations
**Files**: Multiple
**Estimated Time**: 2-3 hours
**Approach**: 
- Add `-> None` to all void functions
- Add parameter type annotations where missing
- Fix generic type parameters

### Task 2: Fix Union Attribute Access
**File**: `src/aibotto/bot/telegram_bot.py`
**Estimated Time**: 3-4 hours
**Approach**:
- Add proper None checks
- Use Optional types correctly
- Add type guards where needed

### Task 3: Fix Return Type Mismatches
**Files**: `src/aibotto/cli/security.py`, `src/aibotto/cli/executor.py`
**Estimated Time**: 2-3 hours
**Approach**:
- Update function signatures to match actual return types
- Fix function logic if needed

### Task 4: Fix Database Layer Typing
**Files**: `src/aibotto/db/models.py`, `src/aibotto/db/operations.py`
**Estimated Time**: 2-3 hours
**Approach**:
- Fix datetime assignment issues
- Add proper type annotations
- Type check database operations

### Task 5: Fix OpenAI API Integration
**Files**: `src/aibotto/ai/llm_client.py`, `src/aibotto/ai/tool_calling.py`
**Estimated Time**: 4-6 hours
**Approach**:
- Research proper OpenAI API typing
- Fix async response typing
- Handle API response structures correctly

### Task 6: Fix Advanced Generic Types
**Files**: `src/aibotto/bot/handlers.py`, `src/aibotto/ai/prompt_templates.py`
**Estimated Time**: 1-2 hours
**Approach**:
- Add proper generic type parameters
- Fix Callable type annotations

## Success Metrics
- All MyPy errors resolved
- Type safety maintained across the codebase
- No regression in functionality
- Improved code maintainability

## Notes
- Start with Phase 1 for quick wins
- Test thoroughly after each phase
- Consider using `# type: ignore` sparingly for complex cases
- Update mypy configuration as needed