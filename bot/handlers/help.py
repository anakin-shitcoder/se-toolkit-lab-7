"""
Handler for /help command.

Provides detailed help information about bot capabilities.
"""

from .base import HandlerResult


def handle_help(args: str = "") -> HandlerResult:
    """
    Handle the /help command.
    
    Args:
        args: Command arguments (can be used for specific help topic)
    
    Returns:
        HandlerResult: Help message
    """
    # Check if user requested help for a specific topic
    topic = args.strip().lower() if args else ""
    
    if topic:
        return _get_topic_help(topic)
    
    message = (
        "📚 Справка по SE Toolkit Bot\n\n"
        "🔹 Команды:\n\n"
        "  /start - Запустить бота и показать приветствие\n"
        "  /help [тема] - Показать справку (опционально по теме)\n"
        "  /labs - Показать список доступных лабораторных работ\n"
        "  /scores - Показать ваши текущие оценки\n"
        "  /health - Проверить статус работы бота\n\n"
        "🔹 Примеры запросов в свободной форме:\n"
        "  • \"Какие у меня оценки?\"\n"
        "  • \"Покажи лабораторные работы\"\n"
        "  • \"Как сдать лабораторную?\"\n\n"
        "🔹 Темы для справки:\n"
        "  • команды - подробнее о командах\n"
        "  • оценки - как работают оценки\n"
        "  • лабораторные - информация о лабораторных работах\n\n"
        "Напишите /help <тема> для получения подробной информации."
    )
    return HandlerResult.ok(message)


def _get_topic_help(topic: str) -> HandlerResult:
    """
    Get help for a specific topic.
    
    Args:
        topic: Topic name
    
    Returns:
        HandlerResult: Topic-specific help message
    """
    topics = {
        "команды": (
            "📋 Доступные команды:\n\n"
            "/start - Запуск бота\n"
            "/help - Справка\n"
            "/labs - Лабораторные работы\n"
            "/scores - Оценки\n"
            "/health - Статус бота"
        ),
        "оценки": (
            "📊 Система оценок:\n\n"
            "Оценки выставляются за выполнение лабораторных работ.\n"
            "Используйте команду /scores для просмотра ваших текущих оценок."
        ),
        "лабораторные": (
            "🔬 Лабораторные работы:\n\n"
            "Список всех доступных работ можно получить через /labs.\n"
            "Каждая работа имеет описание, сроки сдачи и максимальный балл."
        ),
    }
    
    # Try to find matching topic
    for key, message in topics.items():
        if topic in key or key in topic:
            return HandlerResult.ok(message)
    
    return HandlerResult.fail(
        error="unknown_topic",
        message=f"❌ Тема \"{topic}\" не найдена. Используйте /help для списка тем."
    )
