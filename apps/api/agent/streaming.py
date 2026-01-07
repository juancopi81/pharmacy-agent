"""SSE streaming adapter for LangGraph agent events."""

import asyncio
import json
from typing import Any, AsyncGenerator

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, SystemMessage

from apps.api.logging_config import get_logger
from apps.api.schemas import StreamEventType
from apps.api.tracing import TraceContext

logger = get_logger(__name__)


def format_sse_event(event_type: StreamEventType, data: dict) -> str:
    """Format an event as SSE data line."""
    payload = {"type": event_type.value, "data": data}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def convert_messages(messages: list[dict]) -> list[HumanMessage | AIMessage]:
    """
    Convert chat messages to LangChain message format.

    Args:
        messages: List of dicts with 'role' and 'content' keys

    Returns:
        List of LangChain message objects
    """
    lc_messages = []
    for msg in messages:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_messages.append(AIMessage(content=msg["content"]))
    return lc_messages


def _extract_chunk_text(content: Any) -> str:
    """
    Extract text from various chunk content formats.

    Handles string content, list of strings, and list of content part dicts
    (e.g., {"type": "text", "text": "..."} or {"text": "..."}).

    Args:
        content: Chunk content in various formats

    Returns:
        Extracted text as a string
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                # Handle content part dicts: {"type":"text","text":"..."} or {"text":"..."}
                txt = item.get("text")
                if isinstance(txt, str):
                    parts.append(txt)
        return "".join(parts)
    return ""


async def stream_agent_response(
    agent: Any,
    messages: list[dict],
    trace_ctx: TraceContext | None = None,
    user_identifier: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    Stream agent response as SSE events.

    Converts LangGraph astream_events to our SSE format:
    - TOKEN events for streaming text chunks
    - TOOL_CALL events when agent invokes a tool (from on_tool_start)
    - TOOL_RESULT events with tool outputs (from on_tool_end)
    - ERROR events for failures
    - DONE event at completion

    Args:
        agent: Compiled LangGraph agent
        messages: Conversation history as list of dicts
        trace_ctx: Optional trace context for request correlation and timing
        user_identifier: Optional user email/phone for prescription context

    Yields:
        SSE formatted event strings
    """
    # Convert messages to LangChain format
    lc_messages = convert_messages(messages)

    # Inject user context as a system message if user_identifier is provided
    # This is prepended to the conversation so the agent knows who it's helping
    if user_identifier:
        user_context = SystemMessage(
            content=f"## User Context\n"
            f"The current user's identifier for prescription lookups is: {user_identifier}\n"
            f"Use this identifier when calling the prescription_management tool."
        )
        lc_messages = [user_context] + lc_messages

    # Map LangGraph run_id -> TraceContext call_id (handles overlapping/nested calls)
    active_calls: dict[str, int] = {}

    try:
        # Stream using astream_events for fine-grained control
        async for event in agent.astream_events(
            {"messages": lc_messages},
            version="v2",
        ):
            kind = event.get("event")
            run_id = event.get("run_id")
            run_key = str(run_id) if run_id is not None else None

            # Handle streaming tokens from LLM
            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    # Handle content that may be string, list of strings, or list of dicts
                    text = _extract_chunk_text(chunk.content)
                    if text:
                        yield format_sse_event(StreamEventType.TOKEN, {"text": text})

            # Handle tool start - more reliable than parsing tool_call_chunks
            elif kind == "on_tool_start":
                tool_name = event.get("name", "unknown")

                # Record tool start in trace context
                if trace_ctx and run_key:
                    active_calls[run_key] = trace_ctx.start_tool(tool_name)

                yield format_sse_event(
                    StreamEventType.TOOL_CALL,
                    {
                        "tool": tool_name,
                        "input": event.get("data", {}).get("input"),
                    },
                )

            # Handle tool execution results
            elif kind == "on_tool_end":
                tool_name = event.get("name", "unknown")
                tool_output = event.get("data", {}).get("output")

                # Determine status and error info from output
                status = "success"
                error_code = None
                error_message = None
                if isinstance(tool_output, dict) and tool_output.get("success") is False:
                    status = "error"
                    error_code = tool_output.get("error_code")
                    error_message = tool_output.get("error_message")

                # Record tool end in trace context
                if trace_ctx and run_key and run_key in active_calls:
                    call_id = active_calls.pop(run_key)
                    trace_ctx.end_tool(call_id, status=status, error_code=error_code)
                    if status == "error":
                        trace_ctx.add_error(
                            error_code=error_code or "UNKNOWN",
                            message=error_message or "Unknown error",
                            tool_name=tool_name,
                        )

                yield format_sse_event(
                    StreamEventType.TOOL_RESULT,
                    {
                        "tool": tool_name,
                        "result": (
                            tool_output
                            if isinstance(tool_output, dict)
                            else str(tool_output)
                        ),
                    },
                )

            # Handle tool errors (defensive - may not fire but handle if it does)
            elif kind == "on_tool_error":
                tool_name = event.get("name", "unknown")
                error_info = event.get("data", {}).get("error", "Unknown error")

                if trace_ctx and run_key and run_key in active_calls:
                    call_id = active_calls.pop(run_key)
                    trace_ctx.end_tool(call_id, status="error", error_code="TOOL_EXCEPTION")
                    trace_ctx.add_error(
                        error_code="TOOL_EXCEPTION",
                        message=str(error_info),
                        tool_name=tool_name,
                    )

        # Send done event
        yield format_sse_event(StreamEventType.DONE, {})

    except asyncio.CancelledError:
        # Client disconnected - don't treat as error, just clean up
        logger.info("SSE stream cancelled by client")
        raise

    except Exception as e:
        # Record stream-level error
        if trace_ctx:
            trace_ctx.add_error(
                error_code="STREAM_ERROR",
                message=str(e),
                tool_name=None,
            )
        yield format_sse_event(StreamEventType.ERROR, {"message": str(e)})
        yield format_sse_event(StreamEventType.DONE, {})

    finally:
        # Log trace summary at request completion
        if trace_ctx:
            summary = {"event": "request_complete", **trace_ctx.to_summary_dict()}
            logger.info(json.dumps(summary, ensure_ascii=False))
