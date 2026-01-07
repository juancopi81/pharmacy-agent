"""LangGraph pharmacy agent definition - compiled once at startup."""

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from apps.api.agent.prompts import PHARMACY_AGENT_SYSTEM_PROMPT
from apps.api.config import get_settings
from apps.api.logging_config import get_logger
from apps.api.tools import PHARMACY_TOOLS

logger = get_logger(__name__)


def _build_pharmacy_agent():
    """
    Build and compile the pharmacy agent graph.

    Called once at module initialization. The compiled graph is reused
    for all requests. User-specific context (user_identifier) is injected
    at runtime by prepending to the conversation messages.

    Returns:
        Compiled LangGraph agent, or None if API key not configured
    """
    settings = get_settings()

    # Skip compilation if no API key (allows tests to import without failing)
    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not set - agent will fail at runtime")
        return None

    logger.info(f"Compiling pharmacy agent with model: {settings.openai_model}")

    # Initialize LLM with streaming (created once, reused for all requests)
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,  # Deterministic for factual responses
        streaming=True,
    )

    # Create agent with base system prompt
    # User-specific context is injected at runtime via messages
    try:
        agent = create_react_agent(
            model=llm,
            tools=PHARMACY_TOOLS,
            prompt=PHARMACY_AGENT_SYSTEM_PROMPT,
        )
    except TypeError:
        # Fallback for older LangGraph versions that use state_modifier
        def state_modifier(state):
            return {
                "messages": [
                    SystemMessage(content=PHARMACY_AGENT_SYSTEM_PROMPT)
                ] + state["messages"]
            }

        agent = create_react_agent(
            model=llm,
            tools=PHARMACY_TOOLS,
            state_modifier=state_modifier,
        )

    logger.info("Pharmacy agent compiled successfully")
    return agent


# Compile agent once at module initialization
_pharmacy_agent = _build_pharmacy_agent()


def get_pharmacy_agent():
    """
    Get the pre-compiled pharmacy agent.

    Returns:
        The singleton compiled agent instance

    Raises:
        RuntimeError: If agent was not compiled (missing API key)
    """
    if _pharmacy_agent is None:
        raise RuntimeError(
            "Pharmacy agent not compiled. Ensure OPENAI_API_KEY is configured."
        )
    return _pharmacy_agent
