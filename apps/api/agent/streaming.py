"""SSE streaming adapter for LangGraph agent events."""

import json
from typing import Any, AsyncGenerator

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage

from apps.api.schemas import StreamEventType


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


async def stream_agent_response(
    agent: Any,
    messages: list[dict],
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

    Yields:
        SSE formatted event strings
    """
    # Convert messages to LangChain format
    lc_messages = convert_messages(messages)

    try:
        # Stream using astream_events for fine-grained control
        async for event in agent.astream_events(
            {"messages": lc_messages},
            version="v2",
        ):
            kind = event["event"]

            # Handle streaming tokens from LLM
            if kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    # Handle content that may be string or list
                    text = (
                        chunk.content
                        if isinstance(chunk.content, str)
                        else "".join(chunk.content)
                    )
                    if text:
                        yield format_sse_event(StreamEventType.TOKEN, {"text": text})

            # Handle tool start - more reliable than parsing tool_call_chunks
            elif kind == "on_tool_start":
                yield format_sse_event(
                    StreamEventType.TOOL_CALL,
                    {
                        "tool": event.get("name", "unknown"),
                        "input": event["data"].get("input"),
                    },
                )

            # Handle tool execution results
            elif kind == "on_tool_end":
                tool_output = event["data"].get("output")
                yield format_sse_event(
                    StreamEventType.TOOL_RESULT,
                    {
                        "tool": event.get("name", "unknown"),
                        "result": (
                            tool_output
                            if isinstance(tool_output, dict)
                            else str(tool_output)
                        ),
                    },
                )

        # Send done event
        yield format_sse_event(StreamEventType.DONE, {})

    except Exception as e:
        yield format_sse_event(StreamEventType.ERROR, {"message": str(e)})
        yield format_sse_event(StreamEventType.DONE, {})
