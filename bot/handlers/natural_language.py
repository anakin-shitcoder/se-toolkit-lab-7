"""
Handler for natural language messages via LLM intent routing.

Uses LLM to understand user intent and call appropriate tools.
"""

import logging

from config import get_settings
from services.llm_client import LLMClient

from .base import HandlerResult

logger = logging.getLogger(__name__)


def handle_natural_language(message: str) -> HandlerResult:
    """
    Handle a natural language message via LLM routing.

    Args:
        message: User's message text

    Returns:
        HandlerResult: LLM-generated response
    """
    settings = get_settings()

    # Check if LLM is configured
    if not settings.llm_api_key or not settings.llm_api_url:
        return HandlerResult.ok(
            "🤔 Я получил ваше сообщение.\n\n"
            "Для обработки естественного языка необходимо настроить LLM API.\n"
            "Пока используйте команды: /start, /help, /labs, /scores, /health"
        )

    try:
        # Create LLM client
        llm = LLMClient(
            base_url=settings.llm_api_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )

        # Route message through LLM
        response, tool_calls = llm.route_message(message)

        # Log tool calls for debugging
        if tool_calls:
            logger.info(f"LLM called {len(tool_calls)} tools: {[tc.name for tc in tool_calls]}")

        return HandlerResult.ok(response)

    except Exception as e:
        logger.exception(f"Natural language handling failed: {e}")
        return HandlerResult.fail(
            error="llm_error",
            message=f"Ошибка обработки запроса: {e}",
        )
