"""Custom exceptions for pharmacy agent tools."""

from apps.api.tools.schemas import ToolErrorCode


class ToolError(Exception):
    """Tool error with code, message, and optional suggestions."""

    def __init__(
        self,
        code: ToolErrorCode,
        message: str,
        suggestions: list[str] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.suggestions = suggestions
        super().__init__(message)

    def to_dict(self) -> dict:
        """Convert exception to dict for tool response."""
        result = {
            "success": False,
            "error_code": self.code.value,
            "error_message": self.message,
        }
        if self.suggestions:
            result["suggestions"] = self.suggestions
        return result
