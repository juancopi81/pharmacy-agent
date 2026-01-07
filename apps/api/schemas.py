"""Pydantic schemas for API request/response models."""

from enum import Enum

from pydantic import BaseModel, Field


class LanguageMode(str, Enum):
    """Supported language modes."""

    AUTO = "auto"
    EN = "en"
    HE = "he"


class Role(str, Enum):
    """Message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """A single message in the conversation history."""

    role: Role
    content: str


class ChatRequest(BaseModel):
    """Request body for the chat/stream endpoint."""

    messages: list[ChatMessage] = Field(
        ...,
        min_length=1,
        description="Conversation history (required, at least one message)",
    )
    user_identifier: str | None = Field(
        default=None,
        description="Optional user identifier (email or phone) for prescription lookups",
    )
    lang_mode: LanguageMode = Field(
        default=LanguageMode.AUTO,
        description="Language mode: auto (detect from message), en, or he",
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = "ok"
    version: str
    service: str = "pharmacy-agent"


class StreamEventType(str, Enum):
    """Types of events in the SSE stream."""

    TOKEN = "token"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    DONE = "done"
