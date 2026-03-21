"""
LLM (Large Language Model) API client for intent recognition and tool routing.

Uses urllib (standard library) for HTTP requests to minimize dependencies.
"""

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a tool/function call from LLM."""
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """Response from LLM with optional tool calls."""
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    finished: bool = True


# Tool definitions for LLM
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_items",
            "description": "Get list of all labs and tasks",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_learners",
            "description": "Get enrolled students and groups",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pass_rates",
            "description": "Get per-task average scores and attempt counts for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"},
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scores",
            "description": "Get score distribution (4 buckets) for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier"},
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_timeline",
            "description": "Get submissions per day for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier"},
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_groups",
            "description": "Get per-group scores and student counts for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier"},
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_learners",
            "description": "Get top N learners by score for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier"},
                    "limit": {"type": "integer", "description": "Number of learners (default 5)"},
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_completion_rate",
            "description": "Get completion rate percentage for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier"},
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_sync",
            "description": "Trigger ETL sync to refresh data from autochecker",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

SYSTEM_PROMPT = """You are an assistant for a Learning Management System (LMS) Telegram bot.
You have access to tools that fetch data from the LMS backend.
When a user asks a question, decide which tool(s) to call to get the answer.

Available tools:
- get_items: List all labs and tasks
- get_learners: Get enrolled students
- get_pass_rates: Get pass rates for a specific lab (requires "lab" argument)
- get_scores: Get score distribution for a lab
- get_timeline: Get submission timeline for a lab
- get_groups: Get per-group performance for a lab
- get_top_learners: Get top learners for a lab (optional "limit" argument)
- get_completion_rate: Get completion rate for a lab
- trigger_sync: Refresh data from autochecker

For questions like "which lab has the lowest pass rate?", first call get_items to get all labs,
then call get_pass_rates for each lab, then compare and answer.

Respond in JSON format:
{
  "content": "Your response or empty string if calling tools",
  "tool_calls": [
    {"name": "tool_name", "arguments": {"arg": "value"}}
  ]
}

If you can answer directly without tools (e.g., greeting), set tool_calls to empty array.
Respond in Russian language."""


class LLMClientError(Exception):
    """Base exception for LLM client errors."""
    pass


class LLMClient:
    """
    Client for LLM API with tool calling support.
    Uses urllib for HTTP requests (standard library).
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "coder-model",
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize LLM client.

        Args:
            base_url: Base URL of the LLM API
            api_key: API key for authentication
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def _request(self, url: str, data: bytes) -> dict:
        """Make HTTP POST request with JSON data."""
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            return json.loads(response.read().decode())

    def chat(self, messages: list[dict], tools: Optional[list] = None) -> LLMResponse:
        """
        Send chat completion request to LLM.

        Args:
            messages: List of message dicts with "role" and "content"
            tools: Optional list of tool definitions

        Returns:
            LLMResponse with content and optional tool calls
        """
        url = f"{self.base_url}/v1/chat/completions"

        payload = {
            "model": self.model,
            "messages": messages,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            data = self._request(url, json.dumps(payload).encode())
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})

            content = message.get("content", "")
            tool_calls = []

            # Parse tool calls
            for tc in message.get("tool_calls", []):
                func = tc.get("function", {})
                try:
                    args = json.loads(func.get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(ToolCall(
                    name=func.get("name", ""),
                    arguments=args,
                ))

            return LLMResponse(content=content, tool_calls=tool_calls)

        except urllib.error.HTTPError as e:
            logger.error(f"LLM HTTP error: {e.code}")
            return LLMResponse(content=f"LLM error: HTTP {e.code}", finished=True)
        except urllib.error.URLError as e:
            logger.error(f"LLM connection error: {e.reason}")
            return LLMResponse(content=f"LLM connection error: {e.reason}", finished=True)
        except Exception as e:
            logger.exception(f"LLM request failed: {e}")
            return LLMResponse(content=f"LLM error: {e}", finished=True)

    def route_message(self, user_message: str) -> tuple[str, list[ToolCall]]:
        """
        Route a user message through LLM for intent recognition and tool calling.

        Args:
            user_message: User's message text

        Returns:
            Tuple of (response_text, list_of_tool_calls)
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        response = self.chat(messages, tools=TOOLS)

        # If LLM wants to call tools, execute them and continue
        max_iterations = 5
        iteration = 0

        while response.tool_calls and iteration < max_iterations:
            iteration += 1
            tool_results = []

            for tool_call in response.tool_calls:
                result = self._execute_tool(tool_call)
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": f"call_{iteration}",
                    "content": json.dumps(result, ensure_ascii=False),
                })

            # Feed tool results back to LLM
            messages.extend([
                {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": [
                        {
                            "id": f"call_{iteration}",
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in response.tool_calls
                    ],
                },
                *tool_results,
            ])

            response = self.chat(messages, tools=TOOLS)

        return response.content or "Не удалось получить ответ от LLM.", response.tool_calls

    def _execute_tool(self, tool_call: ToolCall) -> dict:
        """
        Execute a tool call against the LMS backend.

        Args:
            tool_call: Tool call with name and arguments

        Returns:
            Tool execution result (JSON-serializable dict)
        """
        # Import settings here to avoid circular imports
        from config import get_settings
        settings = get_settings()
        backend_url = settings.lms_api_url.rstrip("/")

        tool_name = tool_call.name
        args = tool_call.arguments

        try:
            if tool_name == "get_items":
                return self._fetch_json(f"{backend_url}/items/")
            elif tool_name == "get_learners":
                return self._fetch_json(f"{backend_url}/learners/")
            elif tool_name == "get_pass_rates":
                lab = args.get("lab", "")
                return self._fetch_json(f"{backend_url}/analytics/pass-rates?lab={lab}")
            elif tool_name == "get_scores":
                lab = args.get("lab", "")
                return self._fetch_json(f"{backend_url}/analytics/scores?lab={lab}")
            elif tool_name == "get_timeline":
                lab = args.get("lab", "")
                return self._fetch_json(f"{backend_url}/analytics/timeline?lab={lab}")
            elif tool_name == "get_groups":
                lab = args.get("lab", "")
                return self._fetch_json(f"{backend_url}/analytics/groups?lab={lab}")
            elif tool_name == "get_top_learners":
                lab = args.get("lab", "")
                limit = args.get("limit", 5)
                return self._fetch_json(f"{backend_url}/analytics/top-learners?lab={lab}&limit={limit}")
            elif tool_name == "get_completion_rate":
                lab = args.get("lab", "")
                return self._fetch_json(f"{backend_url}/analytics/completion-rate?lab={lab}")
            elif tool_name == "trigger_sync":
                return self._post_json(f"{backend_url}/pipeline/sync", {})
            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.exception(f"Tool execution failed: {tool_name}")
            return {"error": str(e)}

    def _fetch_json(self, url: str) -> dict:
        """Fetch JSON from URL with API key authentication."""
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=10.0) as response:
            data = json.loads(response.read().decode())
            if isinstance(data, dict):
                return data
            return {"data": data}

    def _post_json(self, url: str, data: dict) -> dict:
        """POST JSON to URL with API key authentication."""
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=10.0) as response:
            resp_data = json.loads(response.read().decode())
            if isinstance(resp_data, dict):
                return resp_data
            return {"result": resp_data}

    def is_available(self) -> bool:
        """Check if LLM service is available."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            with urllib.request.urlopen(req, timeout=5.0):
                return True
        except Exception:
            return False
