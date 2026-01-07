"""Pydantic schemas for API request/response models."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


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
    content: str = Field(
        ..., max_length=16000, description="Message content (max 16k characters)"
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Role) -> Role:
        """Only allow user and assistant roles for inbound messages (security)."""
        if v == Role.SYSTEM:
            raise ValueError("System role is not allowed in inbound messages")
        return v


class ChatRequest(BaseModel):
    """Request body for the chat/stream endpoint."""

    messages: list[ChatMessage] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Conversation history (required, 1-100 messages)",
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
