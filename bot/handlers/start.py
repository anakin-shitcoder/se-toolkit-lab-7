"""
Handler for /start command.

Welcomes new users and provides initial guidance.
"""

from .base import HandlerResult


def handle_start(args: str = "") -> HandlerResult:
    """
    Handle the /start command.

    Args:
        args: Command arguments (ignored for start command)

    Returns:
        HandlerResult: Welcome message with inline keyboard
    """
    message = (
        "👋 Добро пожаловать в SE Toolkit Bot!\n\n"
        "Я ваш помощник для управления лабораторными работами.\n\n"
        "📋 Доступные команды:\n"
        "  /help - Показать справку\n"
        "  /labs - Список лабораторных работ\n"
        "  /scores - Мои оценки\n"
        "  /health - Проверка статуса бота\n\n"
        "Также вы можете писать сообщения в свободной форме - "
        "я постараюсь понять ваш запрос и помочь!"
    )
    
    # Inline keyboard for quick actions
    keyboard = [
        [
            {"text": "📚 Labs", "callback_data": "labs"},
            {"text": "📊 Scores", "callback_data": "scores"},
        ],
        [
            {"text": "💚 Health", "callback_data": "health"},
            {"text": "❓ Help", "callback_data": "help"},
        ],
    ]
    
    return HandlerResult.ok(message, keyboard=keyboard)
