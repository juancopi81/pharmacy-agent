"""LangGraph pharmacy agent definition."""

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from apps.api.agent.prompts import get_system_prompt
from apps.api.config import get_settings
from apps.api.logging_config import get_logger
from apps.api.tools import PHARMACY_TOOLS

logger = get_logger(__name__)


def create_pharmacy_agent(user_identifier: str | None = None):
    """
    Create the pharmacy agent graph.

    Uses LangGraph's prebuilt ReAct agent pattern with:
    - OpenAI LLM (model configurable via OPENAI_MODEL env var)
    - The 3 pharmacy tools (medication, inventory, prescription)
    - System prompt for policy enforcement and bilingual support

    Args:
        user_identifier: Optional user email/phone for prescription context

    Returns:
        Compiled LangGraph agent
    """
    settings = get_settings()
    # Log the model and API key
    logger.info(f"Creating pharmacy agent with model: {settings.openai_model}")

    # Initialize LLM with streaming (model configurable via env)
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,  # Deterministic for factual responses
        streaming=True,
    )

    # Get system prompt with optional user context
    system_prompt = get_system_prompt(user_identifier)

    # Create agent with compatibility fallback for different LangGraph versions
    # Some versions accept prompt=, others want state_modifier
    try:
        return create_react_agent(
            model=llm,
            tools=PHARMACY_TOOLS,
            prompt=system_prompt,
        )
    except TypeError:
        # Fallback for older LangGraph versions that use state_modifier
        def state_modifier(state):
            return {
                "messages": [SystemMessage(content=system_prompt)] + state["messages"]
            }

        return create_react_agent(
            model=llm,
            tools=PHARMACY_TOOLS,
            state_modifier=state_modifier,
        )
