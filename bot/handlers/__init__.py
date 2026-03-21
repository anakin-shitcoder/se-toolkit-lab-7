"""
Command handlers for Telegram bot.

This module contains all command handlers. Handlers are pure functions
that take a command string and optional context, and return a text response.
They have no dependency on Telegram or aiogram, making them easily testable.
"""

from typing import Callable

from .base import CommandHandler, HandlerResult
from .start import handle_start
from .help import handle_help
from .health import handle_health
from .labs import handle_labs
from .scores import handle_scores
from .natural_language import handle_natural_language

__all__ = [
    "CommandHandler",
    "HandlerResult",
    "handle_start",
    "handle_help",
    "handle_health",
    "handle_labs",
    "handle_scores",
    "handle_natural_language",
    "get_handler_for_command",
]


def get_handler_for_command(command: str) -> CommandHandler | None:
    """
    Get the handler function for a given command.

    Args:
        command: Command name without leading slash (e.g., "start", "help")

    Returns:
        Handler function or None if command is not recognized
    """
    handlers: dict[str, CommandHandler] = {
        "start": handle_start,
        "help": handle_help,
        "health": handle_health,
        "labs": handle_labs,
        "scores": handle_scores,
    }
    return handlers.get(command.lower())
