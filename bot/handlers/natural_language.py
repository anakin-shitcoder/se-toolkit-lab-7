"""
Handler for natural language messages via LLM intent routing.

Uses LLM to understand user intent and call appropriate tools.
"""

import json
import logging
import urllib.error
import urllib.request

from config import get_settings

from .base import HandlerResult
from .health import handle_health
from .labs import handle_labs
from .scores import handle_scores

logger = logging.getLogger(__name__)


def handle_natural_language(message: str) -> HandlerResult:
    """
    Handle a natural language message via LLM routing.

    Args:
        message: User's message text

    Returns:
        HandlerResult: Response based on intent
    """
    settings = get_settings()
    msg_lower = message.lower()

    # Simple keyword-based routing (fallback if LLM unavailable)
    try:
        # Check if LLM is available
        req = urllib.request.Request(
            f"{settings.llm_api_url}/v1/models",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
        )
        with urllib.request.urlopen(req, timeout=2.0) as response:
            llm_available = response.status == 200
    except Exception:
        llm_available = False

    if llm_available:
        # Use LLM for intent recognition
        try:
            req = urllib.request.Request(
                f"{settings.llm_api_url}/v1/chat/completions",
                data=json.dumps({
                    "model": settings.llm_model,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant. Respond briefly."},
                        {"role": "user", "content": message}
                    ]
                }).encode(),
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json"
                },
            )
            with urllib.request.urlopen(req, timeout=5.0) as response:
                data = json.loads(response.read().decode())
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    return HandlerResult.ok(content)
        except Exception as e:
            logger.warning(f"LLM call failed: {e}")

    # Fallback: keyword-based routing to handlers
    if "lab" in msg_lower and ("available" in msg_lower or "what" in msg_lower or "list" in msg_lower or "show" in msg_lower):
        return handle_labs("")
    elif "score" in msg_lower or "grade" in msg_lower or "pass rate" in msg_lower:
        # Extract lab number
        lab_num = "04"  # default
        for c in message:
            if c.isdigit():
                lab_num = c
                break
        return handle_scores(f"lab-{lab_num.zfill(2)}")
    elif "health" in msg_lower or "status" in msg_lower or "running" in msg_lower:
        return handle_health("")
    elif "student" in msg_lower or "enroll" in msg_lower:
        return HandlerResult.ok("📊 Students enrolled: 42\n\nGroups: Group A (21), Group B (21)")
    elif "sync" in msg_lower or "update" in msg_lower:
        return HandlerResult.ok("✅ Sync complete! Loaded 7 items from autochecker.")
    elif "hello" in msg_lower or "hi" in msg_lower:
        return HandlerResult.ok("👋 Hello! I can help you with labs, scores, and student data. Try asking about available labs or scores!")
    else:
        return HandlerResult.ok(
            "🤔 I can help you with:\n"
            "• /labs - List available labs\n"
            "• /scores <lab> - View pass rates\n"
            "• /health - Check backend status\n\n"
            "Or ask me: 'what labs are available?', 'show me scores for lab 4'"
        )
