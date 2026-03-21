"""
Handler for /health command.

Returns health status of the bot and its dependencies.
"""

import json
import logging
import urllib.error
import urllib.request

from config import get_settings

from .base import HandlerResult

logger = logging.getLogger(__name__)


def handle_health(args: str = "") -> HandlerResult:
    """
    Handle the /health command.

    Args:
        args: Command arguments (ignored for health command)

    Returns:
        HandlerResult: Health status information
    """
    settings = get_settings()
    backend_url = settings.lms_api_url.rstrip("/")

    try:
        # Try to connect to backend using urllib (standard library)
        req = urllib.request.Request(
            f"{backend_url}/items/",
            headers={
                "Authorization": f"Bearer {settings.lms_api_key}",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=5.0) as response:
            data = json.loads(response.read().decode())
            # API can return {"items": [...]} or just [...]
            if isinstance(data, dict):
                items = data.get("items", [])
            elif isinstance(data, list):
                items = data
            else:
                items = []
            item_count = len(items) if isinstance(items, list) else "N/A"
            message = (
                f"✅ Backend здоров\n\n"
                f"📊 Доступно элементов: {item_count}\n"
                f"🔗 URL: {backend_url}"
            )
            return HandlerResult.ok(message)

    except urllib.error.HTTPError as e:
        if e.code == 401:
            return HandlerResult.fail(
                "Backend error: HTTP 401 Unauthorized. Проверьте LMS_API_KEY.",
                message="Ошибка аутентификации в backend.",
            )
        return HandlerResult.fail(
            f"Backend error: HTTP {e.code}. The backend service may be down.",
            message=f"HTTP ошибка: {e.code}",
        )
    except urllib.error.URLError as e:
        reason = str(e.reason)
        return HandlerResult.fail(
            f"Backend error: connection refused ({backend_url}). Check that the services are running.",
            message=f"Не удалось подключиться к backend: {reason}",
        )
    except Exception as e:
        logger.exception(f"Unexpected health check error: {e}")
        return HandlerResult.fail(
            f"Backend error: {str(e)}",
            message=f"Неожиданная ошибка: {str(e)}",
        )
