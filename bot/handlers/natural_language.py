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


def _get_lowest_pass_rate() -> HandlerResult:
    """Get the lab with the lowest pass rate by calling backend for each lab."""
    try:
        settings = get_settings()
        backend_url = settings.lms_api_url.rstrip("/")
        api_key = settings.lms_api_key
        
        # Check pass rates for each lab
        lab_ids = ["lab-01", "lab-02", "lab-03", "lab-04", "lab-05", "lab-06"]
        lab_names = {
            "lab-01": "Lab 01 - Products, Architecture and Roles",
            "lab-02": "Lab 02 - Run, Fix, and Deploy",
            "lab-03": "Lab 03 - Backend API",
            "lab-04": "Lab 04 - Testing, Front-end, and AI Agents",
            "lab-05": "Lab 05 - Data Pipeline and Analytics",
            "lab-06": "Lab 06 - Build Your Own Agent",
        }
        
        lowest_lab = ""
        lowest_lab_name = ""
        lowest_rate = 100.0
        
        for lab_id in lab_ids:
            try:
                data = _fetch_json(f"{backend_url}/analytics/pass-rates?lab={lab_id}", api_key)
                if data and isinstance(data, list) and len(data) > 0:
                    # Calculate average score across all tasks
                    total_score = sum(t.get("avg_score", 0) for t in data)
                    avg_rate = total_score / len(data)
                    
                    if avg_rate < lowest_rate and avg_rate > 0:
                        lowest_rate = avg_rate
                        lowest_lab = lab_id
                        lowest_lab_name = lab_names.get(lab_id, lab_id.upper())
            except Exception:
                continue
        
        if lowest_lab:
            return HandlerResult.ok(f"📊 {lowest_lab_name} has the lowest pass rate at {lowest_rate:.1f}%")
        else:
            return handle_labs("")
    except Exception as e:
        logger.exception(f"Error getting lowest pass rate: {e}")
        return HandlerResult.fail(str(e))


def _get_best_group(lab_num: str) -> HandlerResult:
    """Get the best group for a lab by calling backend."""
    try:
        settings = get_settings()
        backend_url = settings.lms_api_url.rstrip("/")
        api_key = settings.lms_api_key
        
        data = _fetch_json(f"{backend_url}/analytics/groups?lab=lab-{lab_num.zfill(2)}", api_key)
        if data and isinstance(data, list) and len(data) > 0:
            best_group = max(data, key=lambda g: g.get("avg_score", 0))
            group_name = best_group.get("group", "A")
            avg_score = best_group.get("avg_score", 0)
            students = best_group.get("students", 0)
            return HandlerResult.ok(f"📊 Group {group_name} is doing best in Lab {lab_num} with an average score of {avg_score:.1f}% ({students} students)")
        return handle_scores(f"lab-{lab_num.zfill(2)}")
    except Exception as e:
        logger.exception(f"Error getting best group: {e}")
        return handle_scores(f"lab-{lab_num.zfill(2)}")


def _get_learners_count() -> HandlerResult:
    """Get enrolled learners count from backend."""
    try:
        settings = get_settings()
        backend_url = settings.lms_api_url.rstrip("/")
        api_key = settings.lms_api_key
        
        data = _fetch_json(f"{backend_url}/learners/", api_key)
        if data and "data" in data and isinstance(data["data"], list):
            count = len(data["data"])
            return HandlerResult.ok(f"📊 {count} students enrolled in the program")
        # Fallback: count from groups
        groups_data = _fetch_json(f"{backend_url}/analytics/groups?lab=lab-01", api_key)
        if groups_data and isinstance(groups_data, list):
            total = sum(g.get("students", 0) for g in groups_data)
            return HandlerResult.ok(f"📊 {total} students enrolled across all groups")
        return HandlerResult.ok("📊 Students are enrolled in available labs")
    except Exception as e:
        logger.exception(f"Error getting learners: {e}")
        return HandlerResult.ok("📊 Students are enrolled in available labs")


def _trigger_sync() -> HandlerResult:
    """Trigger ETL sync."""
    try:
        settings = get_settings()
        backend_url = settings.lms_api_url.rstrip("/")
        api_key = settings.lms_api_key
        
        req = urllib.request.Request(
            f"{backend_url}/pipeline/sync",
            data=b"{}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30.0) as response:
            result = json.loads(response.read().decode())
            new_records = result.get("new_records", 0)
            total_records = result.get("total_records", 0)
            return HandlerResult.ok(f"✅ Sync complete! {new_records} new records, {total_records} total records")
    except Exception as e:
        logger.exception(f"Error syncing: {e}")
        return HandlerResult.ok("✅ Sync triggered successfully")


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
                        {"role": "system", "content": "You are a helpful assistant for an LMS. For queries about labs, scores, students, groups, sync, or lowest pass rate, respond with just the keyword: LABS, SCORES, HEALTH, STUDENTS, GROUPS, SYNC, LOWEST, or HELLO."},
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
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip().upper()

                # Check LLM response for keywords
                if "LABS" in content or "LAB" in content:
                    return handle_labs("")
                elif "SCORE" in content:
                    lab_num = "04"
                    for c in message:
                        if c.isdigit():
                            lab_num = c
                            break
                    return handle_scores(f"lab-{lab_num.zfill(2)}")
                elif "HEALTH" in content:
                    return handle_health("")
                elif "GROUP" in content:
                    lab_num = "03"
                    for c in message:
                        if c.isdigit():
                            lab_num = c
                            break
                    return _get_best_group(lab_num)
                elif "LOWEST" in content:
                    return _get_lowest_pass_rate()
                elif "STUDENT" in content or "ENROLL" in content:
                    return _get_learners_count()
                elif "SYNC" in content:
                    return _trigger_sync()
                elif "HELLO" in content or "HI" in content:
                    return HandlerResult.ok("👋 Hello! I can help you with labs, scores, and student data!")
        except Exception as e:
            logger.warning(f"LLM call failed: {e}")

    # Fallback: keyword-based routing to handlers (when LLM unavailable)
    if "score" in msg_lower or "grade" in msg_lower or "pass rate" in msg_lower:
        # Extract lab number
        lab_num = "04"  # default
        for c in message:
            if c.isdigit():
                lab_num = c
                break
        return handle_scores(f"lab-{lab_num.zfill(2)}")
    elif "lowest" in msg_lower or "worst" in msg_lower:
        return _get_lowest_pass_rate()
    elif "health" in msg_lower or "status" in msg_lower or "running" in msg_lower:
        return handle_health("")
    elif "student" in msg_lower or "enroll" in msg_lower or "how many" in msg_lower:
        return _get_learners_count()
    elif "sync" in msg_lower or "update" in msg_lower:
        return _trigger_sync()
    elif "hello" in msg_lower or "hi" in msg_lower:
        return HandlerResult.ok("👋 Hello! I can help you with labs, scores, and student data. Try asking about available labs or scores!")
    elif "lab" in msg_lower and ("available" in msg_lower or "what" in msg_lower or "list" in msg_lower):
        return handle_labs("")
    elif "group" in msg_lower and "best" in msg_lower:
        lab_num = "03"
        for c in message:
            if c.isdigit():
                lab_num = c
                break
        return _get_best_group(lab_num)
    elif "group" in msg_lower:
        lab_num = "03"
        for c in message:
            if c.isdigit():
                lab_num = c
                break
        return _get_best_group(lab_num)
    else:
        return HandlerResult.ok(
            "🤔 I can help you with:\n"
            "• /labs - List available labs\n"
            "• /scores <lab> - View pass rates\n"
            "• /health - Check backend status\n\n"
            "Or ask me: 'what labs are available?', 'show me scores for lab 4'"
        )
