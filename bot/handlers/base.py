"""
Base types and interfaces for command handlers.

Defines the contract that all command handlers must follow.
"""

from dataclasses import dataclass, field
from typing import Callable, Protocol


@dataclass
class HandlerResult:
    """
    Result of a command handler execution.

    Attributes:
        success: Whether the handler executed successfully
        message: Text response to send to the user
        error: Error message if success is False
        data: Optional structured data for advanced use cases
        keyboard: Optional inline keyboard markup (list of button rows)
    """
    success: bool = True
    message: str = ""
    error: str | None = None
    data: dict | None = None
    keyboard: list[list[dict]] | None = None

    @classmethod
    def ok(cls, message: str, data: dict | None = None, keyboard: list[list[dict]] | None = None) -> "HandlerResult":
        """Create a successful result."""
        return cls(success=True, message=message, data=data, keyboard=keyboard)

    @classmethod
    def fail(cls, error: str, message: str = "") -> "HandlerResult":
        """Create a failed result."""
        return cls(success=False, message=message or "Operation failed", error=error)


class CommandHandler(Protocol):
    """
    Protocol for command handler functions.

    Handlers are pure functions that process commands and return results.
    They should not have side effects or dependencies on Telegram APIs.
    """

    def __call__(self, args: str = "") -> HandlerResult:
        """
        Execute the command handler.

        Args:
            args: Command arguments as a string (everything after the command)

        Returns:
            HandlerResult: Result of command execution
        """
        ...


# Type alias for handler functions
HandlerFunc = Callable[[str], HandlerResult]
