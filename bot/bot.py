#!/usr/bin/env python3
"""
Telegram Bot Entry Point.

Supports two modes:
1. Normal mode: Runs the bot with aiogram to handle Telegram updates
2. Test mode (--test): Executes a command handler and prints result to stdout

Usage:
    python bot.py              # Run bot in normal mode
    python bot.py --test "/start"   # Test /start command
"""

import argparse
import asyncio
import logging
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import Message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_test_command(test_arg: str) -> tuple[str, str]:
    """
    Parse test command argument.
    
    Args:
        test_arg: Command string (e.g., "/start", "/labs 1")
    
    Returns:
        Tuple of (command_name, arguments)
    """
    # Remove leading slash if present
    cmd = test_arg.strip()
    if cmd.startswith("/"):
        cmd = cmd[1:]
    
    # Split command and arguments
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    return command, args


def run_test_mode(command: str, args: str) -> int:
    """
    Run a command handler in test mode.

    Args:
        command: Command name (without slash)
        args: Command arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Lazy imports for test mode (no aiogram dependency)
    from handlers import get_handler_for_command, HandlerResult, handle_natural_language

    # Check if this is a natural language message (doesn't start with known command)
    if command not in ["start", "help", "health", "labs", "scores"]:
        # Treat as natural language message
        logger.info(f"Natural language query: {command} {args}".strip())
        full_message = f"{command} {args}".strip()
        result: HandlerResult = handle_natural_language(full_message)
        if result.success:
            print(result.message)
            return 0
        else:
            print(f"Error: {result.error}")
            if result.message:
                print(result.message)
            return 1

    logger.info(f"Testing command: {command} with args: {args!r}")

    # Get handler for command
    handler = get_handler_for_command(command)

    if handler is None:
        print(f"❌ Unknown command: /{command}")
        print(f"Available commands: start, help, health, labs, scores")
        return 1

    # Execute handler
    try:
        result = handler(args)

        # Print result
        if result.success:
            print(result.message)
            return 0
        else:
            print(f"Error: {result.error}")
            if result.message:
                print(result.message)
            return 1

    except Exception as e:
        logger.exception(f"Handler execution failed: {e}")
        print(f"❌ Handler error: {e}")
        return 1


async def run_bot() -> None:
    """Run the Telegram bot in normal mode."""
    # Lazy imports for normal mode only
    from aiogram import Bot, Dispatcher
    from aiogram.filters import Command, CommandStart

    from config import get_settings

    settings = get_settings()

    if not settings.is_configured:
        logger.error(
            "Bot is not configured. Please set TELEGRAM_BOT_TOKEN "
            "in .env.bot.secret or .env.bot.example"
        )
        sys.exit(1)

    # Initialize bot and dispatcher
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()

    # Register command handlers
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_health, Command("health"))
    dp.message.register(cmd_labs, Command("labs"))
    dp.message.register(cmd_scores, Command("scores"))
    dp.message.register(handle_message)

    logger.info(f"Starting bot: {settings.bot_name}")

    # Start polling
    await dp.start_polling(bot)


async def cmd_start(message: "Message") -> None:
    """Handle /start command from Telegram."""
    from handlers import handle_start

    result = handle_start()
    await send_handler_result(message, result)


async def cmd_help(message: "Message") -> None:
    """Handle /help command from Telegram."""
    from handlers import handle_help

    # Extract arguments from message text
    args = extract_command_args(message.text or "")
    result = handle_help(args)
    await send_handler_result(message, result)


async def cmd_health(message: "Message") -> None:
    """Handle /health command from Telegram."""
    from handlers import handle_health

    result = handle_health()
    await send_handler_result(message, result)


async def cmd_labs(message: "Message") -> None:
    """Handle /labs command from Telegram."""
    from handlers import handle_labs

    args = extract_command_args(message.text or "")
    result = handle_labs(args)
    await send_handler_result(message, result)


async def cmd_scores(message: "Message") -> None:
    """Handle /scores command from Telegram."""
    from handlers import handle_scores

    args = extract_command_args(message.text or "")
    result = handle_scores(args)
    await send_handler_result(message, result)


async def handle_message(message: "Message") -> None:
    """
    Handle regular messages (for LLM intent recognition).

    In production, this would use LLMClient to recognize intent
    and route to appropriate handler.
    """
    # Placeholder - LLM integration will be added in Task 3
    await message.answer(
        "🤔 Я получил ваше сообщение. В будущей версии я буду "
        "понимать естественный язык и отвечать на ваши вопросы!\n\n"
        "Пока используйте команды: /start, /help, /labs, /scores, /health"
    )


async def send_handler_result(message: "Message", result: HandlerResult) -> None:
    """
    Send handler result to Telegram chat.

    Args:
        message: Original message
        result: Handler result to send
    """
    if result.success:
        await message.answer(result.message)
    else:
        await message.answer(f"❌ {result.message}")


def extract_command_args(text: str) -> str:
    """
    Extract arguments from a command message.
    
    Args:
        text: Full message text (e.g., "/labs 1")
    
    Returns:
        Command arguments (e.g., "1")
    """
    parts = text.split(maxsplit=1)
    return parts[1] if len(parts) > 1 else ""


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="SE Toolkit Telegram Bot"
    )
    parser.add_argument(
        "--test",
        type=str,
        metavar="COMMAND",
        help="Run a command in test mode (e.g., --test '/start')",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    args = parser.parse_args()
    
    # Configure debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Test mode
    if args.test:
        command, cmd_args = parse_test_command(args.test)
        return run_test_mode(command, cmd_args)
    
    # Normal mode - run bot
    try:
        asyncio.run(run_bot())
        return 0
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        return 0
    except Exception as e:
        logger.exception(f"Bot crashed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
