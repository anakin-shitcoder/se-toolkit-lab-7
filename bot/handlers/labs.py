"""
Handler for /labs command.

Returns list of available lab assignments.
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


def handle_labs(args: str = "") -> HandlerResult:
    """
    Handle the /labs command.

    Args:
        args: Command arguments (can be used for specific lab lookup)

    Returns:
        HandlerResult: List of lab assignments
    """
    # Check if user requested a specific lab
    lab_arg = args.strip() if args else ""

    if lab_arg:
        return _get_specific_lab(lab_arg)

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

        # Group items by lab
        labs_dict = {}
        for item in items:
            lab_id = item.get("lab_id", "")
            if lab_id:
                if lab_id not in labs_dict:
                    labs_dict[lab_id] = {
                        "title": item.get("lab_title", lab_id),
                        "tasks": [],
                    }
                labs_dict[lab_id]["tasks"].append(item)

        lines = ["🔬 Доступные лабораторные работы:\n"]
        for i, (lab_id, lab_data) in enumerate(sorted(labs_dict.items()), 1):
            title = lab_data["title"]
            task_count = len(lab_data["tasks"])
            lines.append(f"{i}. {title}")
            lines.append(f"   Заданий: {task_count}")
            lines.append("")

        message = "\n".join(lines)
        if len(lines) > 1:
            message += "\n💡 Используйте /scores <lab> для просмотра оценок."
        return HandlerResult.ok(message)

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
    except urllib.error.URLError as e:
        return HandlerResult.fail(
            f"Backend error: connection refused ({backend_url}). Check that the services are running.",
            message=f"Не удалось подключиться к backend.",
        )
    except Exception as e:
        logger.exception(f"Unexpected labs fetch error: {e}")
        return HandlerResult.fail(
            f"Backend error: {str(e)}",
            message=f"Неожиданная ошибка: {str(e)}",
        )


def _get_specific_lab(lab_arg: str) -> HandlerResult:
    """
    Get details for a specific lab.

    Args:
        lab_arg: Lab number or identifier

    Returns:
        HandlerResult: Lab details
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
        data = _fetch_json(f"{backend_url}/items/", settings.lms_api_key)
        # API can return {"items": [...]} or just [...]
        if isinstance(data, dict):
            items = data.get("items", [])
        elif isinstance(data, list):
            items = data
        else:
            items = []

        # Filter items for this lab
        lab_items = [item for item in items if item.get("lab_id", "").lower() == lab_id]

        if not lab_items:
            return HandlerResult.fail(
                error="lab_not_found",
                message=f"❌ Лабораторная работа \"{lab_arg}\" не найдена.",
            )

        lab_title = lab_items[0].get("lab_title", lab_id)
        lines = [f"🔬 {lab_title}\n", "Задания:\n"]

        for item in lab_items:
            task_title = item.get("title", "Без названия")
            task_type = item.get("type", "unknown")
            lines.append(f"• {task_title}")
            lines.append(f"  Тип: {task_type}")
            lines.append("")

        return HandlerResult.ok("\n".join(lines))

    except urllib.error.HTTPError as e:
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
        logger.exception(f"Unexpected lab fetch error: {e}")
        return HandlerResult.fail(
            f"Backend error: {str(e)}",
            message=f"Неожиданная ошибка: {str(e)}",
        )
