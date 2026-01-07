"""Request tracing infrastructure for correlation IDs and timing."""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """Timing information for a single tool execution."""

    call_id: int
    tool_name: str
    start_time: float  # perf_counter value
    end_time: float | None = None
    status: str = "in_progress"
    error_code: str | None = None

    @property
    def latency_ms(self) -> float | None:
        """Calculate latency in milliseconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization."""
        latency = self.latency_ms
        return {
            "call_id": self.call_id,
            "tool": self.tool_name,
            "latency_ms": round(latency, 2) if latency is not None else None,
            "status": self.status,
            "error_code": self.error_code,
        }


@dataclass
class TraceContext:
    """Context for a single request trace."""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: float = field(default_factory=time.perf_counter)
    user_id: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    _next_call_id: int = field(default=1, repr=False)

    def start_tool(self, tool_name: str) -> int:
        """
        Record tool execution start.

        Args:
            tool_name: Name of the tool being called

        Returns:
            call_id for use with end_tool()
        """
        call_id = self._next_call_id
        self._next_call_id += 1

        self.tool_calls.append(
            ToolCall(
                call_id=call_id,
                tool_name=tool_name,
                start_time=time.perf_counter(),
            )
        )
        return call_id

    def end_tool(
        self,
        call_id: int,
        status: str = "success",
        error_code: str | None = None,
    ) -> None:
        """
        Record tool execution end.

        Args:
            call_id: The call_id returned by start_tool()
            status: "success" or "error"
            error_code: Error code if status is "error"
        """
        for tool_call in self.tool_calls:
            if tool_call.call_id == call_id:
                tool_call.end_time = time.perf_counter()
                tool_call.status = status
                tool_call.error_code = error_code
                break

    def add_error(
        self,
        error_code: str,
        message: str,
        tool_name: str | None = None,
    ) -> None:
        """
        Record an error.

        Args:
            error_code: Error code (e.g., "NOT_FOUND", "STREAM_ERROR")
            message: Human-readable error message
            tool_name: Name of tool that caused the error (if applicable)
        """
        self.errors.append(
            {
                "error_code": error_code,
                "message": message,
                "tool_name": tool_name,
                "timestamp": time.time(),
            }
        )

    @property
    def tools_called(self) -> list[str]:
        """Get ordered list of tool names called."""
        return [tc.tool_name for tc in self.tool_calls]

    @property
    def total_latency_ms(self) -> float:
        """Calculate total request latency in milliseconds."""
        return (time.perf_counter() - self.start_time) * 1000

    def to_summary_dict(self) -> dict[str, Any]:
        """
        Generate structured JSON summary for logging.

        Returns:
            Dict with all trace information for JSON serialization
        """
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "tools_called": self.tools_called,
            "tool_details": [tc.to_dict() for tc in self.tool_calls],
            "total_latency_ms": round(self.total_latency_ms, 2),
            "success": len(self.errors) == 0,
            "errors": self.errors if self.errors else None,
        }
