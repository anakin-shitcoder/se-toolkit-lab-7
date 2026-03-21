"""
Handler for /scores command.

Returns user's current scores/grades.
"""

import json
import logging
import urllib.error
import urllib.request

from config import get_settings

from .base import HandlerResult

logger = logging.getLogger(__name__)


def _fetch_json(url: str, api_key: str) -> dict:
    """Fetch JSON from URL with API key authentication."""
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=10.0) as response:
        return json.loads(response.read().decode())


def handle_scores(args: str = "") -> HandlerResult:
    """
    Handle the /scores command.

    Args:
        args: Command arguments (can be used for specific lab score lookup)

    Returns:
        HandlerResult: User's scores information
    """
    # Check if user requested scores for a specific lab
    lab_arg = args.strip() if args else ""

    if lab_arg:
        return _get_specific_score(lab_arg)

    settings = get_settings()
    backend_url = settings.lms_api_url.rstrip("/")

    try:
        data = _fetch_json(f"{backend_url}/items/", settings.lms_api_key)
        # API can return {"items": [...]} or just [...]
        if isinstance(data, dict):
            items = data.get("items", [])
        elif isinstance(data, list):
            items = data
        else:
            items = []

        if not items:
            return HandlerResult.ok("ℹ️ Лабораторные работы пока не добавлены.")

        # Group by lab and show pass rates
        labs_dict = {}
        for item in items:
            lab_id = item.get("lab_id", "")
            if lab_id:
                if lab_id not in labs_dict:
                    labs_dict[lab_id] = {
                        "title": item.get("lab_title", lab_id),
                        "tasks": [],
                    }
                labs_dict[lab_id]["tasks"].append(item.get("title", "Без названия"))

        lines = ["📊 Доступные лабораторные работы:\n"]
        for lab_id, lab_data in sorted(labs_dict.items()):
            title = lab_data["title"]
            task_count = len(lab_data["tasks"])
            lines.append(f"• {title} ({task_count} заданий)")

        lines.append("\n💡 Используйте /scores <lab> для просмотра оценок.")
        lines.append("   Например: /scores lab-04")

        return HandlerResult.ok("\n".join(lines))

    except urllib.error.HTTPError as e:
        if e.code == 401:
            return HandlerResult.fail(
                "Backend error: HTTP 401 Unauthorized. Проверьте LMS_API_KEY.",
                message="Ошибка аутентификации в backend.",
            )
        return HandlerResult.fail(
            f"Backend error: HTTP {e.code}",
            message=f"Backend вернул неожиданный статус: {e.code}",
        )
    except urllib.error.URLError:
        return HandlerResult.fail(
            f"Backend error: connection refused ({backend_url}). Check that the services are running.",
            message="Не удалось подключиться к backend.",
        )
    except Exception as e:
        logger.exception(f"Unexpected scores fetch error: {e}")
        return HandlerResult.fail(
            f"Backend error: {str(e)}",
            message=f"Неожиданная ошибка: {str(e)}",
        )


def _get_specific_score(lab_arg: str) -> HandlerResult:
    """
    Get score for a specific lab.

    Args:
        lab_arg: Lab identifier (e.g., "lab-04", "4")

    Returns:
        HandlerResult: Lab score details with pass rates
    """
    settings = get_settings()
    backend_url = settings.lms_api_url.rstrip("/")

    # Normalize lab argument to lab-XX format
    if lab_arg.isdigit():
        lab_id = f"lab-{int(lab_arg):02d}"
    elif not lab_arg.lower().startswith("lab-"):
        lab_id = f"lab-{lab_arg.zfill(2)}"
    else:
        lab_id = lab_arg.lower()

    try:
        # Get pass rates for this lab
        data = _fetch_json(
            f"{backend_url}/analytics/pass-rates?lab={lab_id}",
            settings.lms_api_key,
        )
        pass_rates = data.get("pass_rates", [])

        if not pass_rates:
            # Try to get lab info at least
            items_data = _fetch_json(f"{backend_url}/items/", settings.lms_api_key)
            # API can return {"items": [...]} or just [...]
            if isinstance(items_data, dict):
                items = items_data.get("items", [])
            elif isinstance(items_data, list):
                items = items_data
            else:
                items = []
            lab_items = [i for i in items if i.get("lab_id", "").lower() == lab_id]
            if lab_items:
                title = lab_items[0].get("lab_title", lab_id)
                return HandlerResult.ok(
                    f"📊 {title}\n\n"
                    f"ℹ️ Статистика пока недоступна.\n"
                    f"Заданий: {len(lab_items)}"
                )
            return HandlerResult.fail(
                error="no_data",
                message=f"ℹ️ Статистика по \"{lab_id}\" пока недоступна.",
            )

        # Format pass rates
        lab_title = pass_rates[0].get("lab_title", lab_id) if pass_rates else lab_id
        lines = [f"📊 {lab_title}\n", "Процент сдачи:\n"]

        for task in pass_rates:
            task_name = task.get("task_title", task.get("task_id", "Без названия"))
            pass_rate = task.get("pass_rate", 0)
            attempts = task.get("attempts", 0)
            lines.append(f"• {task_name}: {pass_rate:.1f}% ({attempts} попыток)")

        return HandlerResult.ok("\n".join(lines))

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return HandlerResult.fail(
                error="lab_not_found",
                message=f"❌ Лабораторная работа \"{lab_arg}\" не найдена.",
            )
        if e.code == 401:
            return HandlerResult.fail(
                "Backend error: HTTP 401 Unauthorized.",
                message="Ошибка аутентификации.",
            )
        return HandlerResult.fail(
            f"Backend error: HTTP {e.code}",
            message=f"Backend вернул статус: {e.code}",
        )
    except urllib.error.URLError:
        return HandlerResult.fail(
            f"Backend error: connection refused ({backend_url}).",
            message="Не удалось подключиться к backend.",
        )
    except Exception as e:
        logger.exception(f"Unexpected score fetch error: {e}")
        return HandlerResult.fail(
            f"Backend error: {str(e)}",
            message=f"Неожиданная ошибка: {str(e)}",
        )
