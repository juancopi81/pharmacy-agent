"""
Pharmacy Agent API - Main Application

A stateless AI pharmacy agent providing medication information,
inventory checks, and prescription management via streaming chat.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from apps.api.agent import create_pharmacy_agent, stream_agent_response
from apps.api.config import get_settings
from apps.api.logging_config import get_logger, setup_logging
from apps.api.schemas import ChatRequest, HealthResponse
from apps.api.tracing import TraceContext

setup_logging()
logger = get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    logger.info("Starting Pharmacy Agent API...")
    logger.info(f"Version: {settings.app_version}")

    yield

    logger.info("Shutting down Pharmacy Agent API...")


app = FastAPI(
    title=settings.app_name,
    description="Real-time AI pharmacy agent for medication info, inventory, and prescriptions",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

WEB_DIR = Path(__file__).parent.parent / "web"
if WEB_DIR.exists() and any(WEB_DIR.iterdir()):
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")
    logger.info(f"Static files mounted from {WEB_DIR}")


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the chat UI or a placeholder if UI is not yet available."""
    index_path = WEB_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))

    placeholder_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pharmacy Agent</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: #f5f5f5;
            }
            .container {
                text-align: center;
                padding: 40px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #333; margin-bottom: 10px; }
            p { color: #666; }
            .status { color: #22c55e; font-weight: bold; }
            a { color: #3b82f6; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Pharmacy Agent</h1>
            <p class="status">API is running</p>
            <p>Chat UI coming soon...</p>
            <p><a href="/docs">API Documentation</a></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=placeholder_html)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for monitoring and container orchestration."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        service="pharmacy-agent",
    )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """
    Streaming chat endpoint for conversational AI interactions.

    This endpoint accepts a conversation history and returns a stream
    of Server-Sent Events (SSE) containing:
    - token: Individual text tokens from the assistant
    - tool_call: When the agent invokes a tool
    - tool_result: Results from tool execution
    - error: Any errors that occur
    - done: Marks end of stream
    """
    # Initialize trace context for request correlation
    trace_ctx = TraceContext(user_id=request.user_identifier)

    logger.info(
        f"Chat request: {len(request.messages)} messages, "
        f"has_user_identifier={request.user_identifier is not None}, "
        f"request_id={trace_ctx.request_id}"
    )

    # Convert ChatMessage to dict format for agent
    messages = [
        {"role": msg.role.value, "content": msg.content} for msg in request.messages
    ]

    # Create agent with optional user context for prescriptions
    agent = create_pharmacy_agent(user_identifier=request.user_identifier)

    return StreamingResponse(
        stream_agent_response(agent=agent, messages=messages, trace_ctx=trace_ctx),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Request-ID": trace_ctx.request_id,
        },
    )
