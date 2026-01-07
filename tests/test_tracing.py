"""Tests for request tracing infrastructure."""

import time
import uuid
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app
from apps.api.tracing import TraceContext, ToolCall


class TestToolCall:
    """Unit tests for ToolCall dataclass."""

    def test_latency_ms_when_incomplete(self):
        """Latency should be None when end_time is not set."""
        tc = ToolCall(call_id=1, tool_name="test_tool", start_time=time.perf_counter())
        assert tc.latency_ms is None

    def test_latency_ms_when_complete(self):
        """Latency should be positive when end_time is set."""
        start = time.perf_counter()
        time.sleep(0.01)  # 10ms
        end = time.perf_counter()

        tc = ToolCall(call_id=1, tool_name="test_tool", start_time=start, end_time=end)
        assert tc.latency_ms is not None
        assert tc.latency_ms > 0

    def test_to_dict_structure(self):
        """Verify to_dict returns expected fields."""
        tc = ToolCall(
            call_id=1,
            tool_name="get_medication_by_name",
            start_time=0.0,
            end_time=0.015,
            status="success",
            error_code=None,
        )
        result = tc.to_dict()

        assert result["call_id"] == 1
        assert result["tool"] == "get_medication_by_name"
        assert result["status"] == "success"
        assert result["error_code"] is None
        assert "latency_ms" in result


class TestTraceContext:
    """Unit tests for TraceContext dataclass."""

    def test_request_id_is_uuid(self):
        """Verify request_id is a valid UUID."""
        ctx = TraceContext()
        # Should not raise ValueError
        parsed = uuid.UUID(ctx.request_id)
        assert str(parsed) == ctx.request_id

    def test_start_tool_returns_call_id(self):
        """Verify start_tool returns incrementing call IDs."""
        ctx = TraceContext()
        id1 = ctx.start_tool("tool_a")
        id2 = ctx.start_tool("tool_b")
        id3 = ctx.start_tool("tool_a")  # Same tool again

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_end_tool_by_call_id(self):
        """Verify end_tool completes the correct call."""
        ctx = TraceContext()
        id1 = ctx.start_tool("tool_a")
        id2 = ctx.start_tool("tool_b")

        # End tool_b first (out of order)
        ctx.end_tool(id2, status="success")
        # End tool_a
        ctx.end_tool(id1, status="error", error_code="NOT_FOUND")

        # Verify correct calls were updated
        assert ctx.tool_calls[0].status == "error"
        assert ctx.tool_calls[0].error_code == "NOT_FOUND"
        assert ctx.tool_calls[1].status == "success"
        assert ctx.tool_calls[1].error_code is None

    def test_multiple_same_tool_calls(self):
        """Verify multiple calls to same tool are tracked separately."""
        ctx = TraceContext()
        id1 = ctx.start_tool("get_medication_by_name")
        ctx.end_tool(id1, status="success")
        id2 = ctx.start_tool("get_medication_by_name")
        ctx.end_tool(id2, status="error", error_code="NOT_FOUND")

        assert len(ctx.tool_calls) == 2
        assert ctx.tool_calls[0].call_id == 1
        assert ctx.tool_calls[0].status == "success"
        assert ctx.tool_calls[1].call_id == 2
        assert ctx.tool_calls[1].status == "error"

    def test_tool_error_recording(self):
        """Verify error recording in trace context."""
        ctx = TraceContext()
        ctx.add_error("NOT_FOUND", "Medication not found", "check_inventory")

        assert len(ctx.errors) == 1
        assert ctx.errors[0]["error_code"] == "NOT_FOUND"
        assert ctx.errors[0]["message"] == "Medication not found"
        assert ctx.errors[0]["tool_name"] == "check_inventory"
        assert "timestamp" in ctx.errors[0]

    def test_latency_is_positive(self):
        """Verify total_latency_ms is positive."""
        ctx = TraceContext()
        time.sleep(0.001)  # 1ms
        assert ctx.total_latency_ms > 0

    def test_tools_called_property(self):
        """Verify tools_called returns ordered list of tool names."""
        ctx = TraceContext()
        ctx.start_tool("tool_a")
        ctx.start_tool("tool_b")
        ctx.start_tool("tool_a")

        assert ctx.tools_called == ["tool_a", "tool_b", "tool_a"]

    def test_summary_dict_structure(self):
        """Verify summary dict has required fields."""
        ctx = TraceContext(user_id="test@example.com")
        call_id = ctx.start_tool("test_tool")
        ctx.end_tool(call_id)

        summary = ctx.to_summary_dict()

        assert "request_id" in summary
        assert "user_id" in summary
        assert "tools_called" in summary
        assert "tool_details" in summary
        assert "total_latency_ms" in summary
        assert "success" in summary
        assert "errors" in summary

        assert summary["user_id"] == "test@example.com"
        assert summary["tools_called"] == ["test_tool"]
        assert summary["success"] is True
        assert summary["errors"] is None

    def test_summary_dict_with_errors(self):
        """Verify summary dict shows success=False when errors exist."""
        ctx = TraceContext()
        ctx.add_error("TEST_ERROR", "Test error message")

        summary = ctx.to_summary_dict()

        assert summary["success"] is False
        assert len(summary["errors"]) == 1


@pytest.mark.asyncio
class TestIntegrationTracing:
    """Integration tests for tracing with the chat endpoint."""

    async def test_x_request_id_header_present(self, test_db):
        """Verify X-Request-ID header is in response."""

        async def fake_stream(*args, **kwargs):
            yield 'data: {"type": "done", "data": {}}\n\n'

        with patch("apps.api.main.stream_agent_response", return_value=fake_stream()):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/chat/stream",
                    json={"messages": [{"role": "user", "content": "Hello"}]},
                )

                assert "X-Request-ID" in response.headers
                # Verify it's a valid UUID
                request_id = response.headers["X-Request-ID"]
                uuid.UUID(request_id)  # Raises if invalid

    async def test_x_request_id_unique_per_request(self, test_db):
        """Verify each request gets a unique X-Request-ID."""

        async def fake_stream(*args, **kwargs):
            yield 'data: {"type": "done", "data": {}}\n\n'

        request_ids = []

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            for _ in range(3):
                # Need fresh mock for each request
                with patch(
                    "apps.api.main.stream_agent_response",
                    return_value=fake_stream(),
                ):
                    response = await client.post(
                        "/chat/stream",
                        json={"messages": [{"role": "user", "content": "Hello"}]},
                    )
                    request_ids.append(response.headers["X-Request-ID"])

        # All request IDs should be unique
        assert len(set(request_ids)) == 3


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database with seeded data."""
    import os
    import sqlite3
    import tempfile
    from pathlib import Path

    from tests.test_tools.conftest import create_test_schema, seed_test_data

    # Create temp file
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Create and seed database
    conn = sqlite3.connect(db_path)
    try:
        create_test_schema(conn)
        seed_test_data(conn)
        conn.commit()
    finally:
        conn.close()

    # Set environment variable for database path
    old_db_path = os.environ.get("DB_PATH")
    os.environ["DB_PATH"] = db_path

    # Clear cached settings to pick up new DB_PATH
    from apps.api.config import get_settings

    get_settings.cache_clear()

    yield db_path

    # Cleanup
    if old_db_path:
        os.environ["DB_PATH"] = old_db_path
    else:
        os.environ.pop("DB_PATH", None)

    get_settings.cache_clear()

    # Remove temp database
    Path(db_path).unlink(missing_ok=True)
