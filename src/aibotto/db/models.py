"""
Enhanced database models for agentic framework.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Conversation:
    """Model for conversation sessions."""

    id: int | None = None
    user_id: int = 0
    chat_id: int = 0
    started_at: datetime | None = None
    ended_at: datetime | None = None
    metadata: str | None = None

    def __post_init__(self) -> None:
        if self.started_at is None:
            self.started_at = datetime.now()


@dataclass
class Message:
    """Model for messages with agentic context."""

    id: int | None = None
    conversation_id: int = 0
    role: str = ""
    content: str = ""
    message_type: str = "chat"
    source_agent: str | None = None
    subagent_instance_id: int | None = None
    iteration_number: int | None = None
    tool_call_id: str | None = None
    telegram_message_id: int | None = None
    timestamp: datetime | None = None
    metadata: str | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ToolCall:
    """Model for tool execution tracking."""

    id: int | None = None
    message_id: int = 0
    tool_name: str = ""
    tool_call_id: str = ""
    arguments_json: str = ""
    result_content: str | None = None
    status: str = "pending"
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None
    source_agent: str = ""
    subagent_instance_id: int | None = None
    iteration_number: int | None = None


@dataclass
class SubAgent:
    """Model for subagent instance tracking."""

    id: int | None = None
    subagent_name: str = ""
    instance_id: int = 0
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: str = "idle"
    max_iterations: int = 5
    actual_iterations: int = 0
    parent_agent: str | None = None
    conversation_id: int | None = None
    user_id: int = 0
    chat_id: int = 0
    task_description: str | None = None
    result_summary: str | None = None
    error_message: str | None = None
    metadata: str | None = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Delegation:
    """Model for delegation events."""

    id: int | None = None
    message_id: int = 0
    parent_agent: str = ""
    parent_subagent_id: int | None = None
    child_agent_name: str = ""
    child_subagent_id: int = 0
    method_name: str | None = None
    task_description: str = ""
    delegated_at: datetime | None = None
    completed_at: datetime | None = None
    status: str = "pending"
    result_content: str | None = None
    error_message: str | None = None
    conversation_id: int = 0
    user_id: int = 0
    chat_id: int = 0
    iteration_number: int | None = None

    def __post_init__(self) -> None:
        if self.delegated_at is None:
            self.delegated_at = datetime.now()


@dataclass
class UserAspect:
    """Model for storing discovered user aspects."""

    id: int | None = None
    user_id: int = 0
    category: str = ""
    aspect: str = ""
    confidence: float = 0.5
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
