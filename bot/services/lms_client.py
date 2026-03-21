"""
LMS (Learning Management System) API client.

Provides methods for fetching student data, lab assignments, and scores.
Uses urllib (standard library) for HTTP requests.
"""

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class LabAssignment:
    """Represents a lab assignment."""
    id: str
    title: str
    description: str
    due_date: str
    max_score: int
    status: str  # "available", "submitted", "graded", "locked"


@dataclass
class Score:
    """Represents a student's score for a lab."""
    lab_id: str
    lab_title: str
    score: Optional[int]
    max_score: int
    status: str  # "not_starts", "in_progress", "submitted", "graded"
    feedback: Optional[str] = None


class LMSClientError(Exception):
    """Base exception for LMS client errors."""
    pass


class LMSClientAuthenticationError(LMSClientError):
    """Raised when authentication fails."""
    pass


class LMSClientNetworkError(LMSClientError):
    """Raised when network request fails."""
    pass


class LMSClient:
    """
    Client for LMS backend API.

    Handles authentication, retries, and caching for API requests.
    Uses urllib for HTTP requests (standard library).
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize LMS client.

        Args:
            base_url: Base URL of the LMS API
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Make an HTTP request.

        Args:
            method: HTTP method
            endpoint: API endpoint (relative to base_url)
            data: Optional JSON data for POST/PUT requests

        Returns:
            Response JSON as dictionary

        Raises:
            LMSClientAuthenticationError: If authentication fails
            LMSClientNetworkError: If network request fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        try:
            if data is not None:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode(),
                    headers=headers,
                    method=method,
                )
            else:
                req = urllib.request.Request(url, headers=headers, method=method)

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode())

        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise LMSClientAuthenticationError(
                    f"Authentication failed: {e.code}"
                )
            raise LMSClientNetworkError(f"HTTP error: {e.code}")
        except urllib.error.URLError as e:
            raise LMSClientNetworkError(f"Network error: {e.reason}")

    def get_labs(self) -> list[LabAssignment]:
        """Fetch all lab assignments."""
        try:
            data = self._request("GET", "/api/labs")
            labs_data = data.get("labs", []) if isinstance(data, dict) else data
            return [
                LabAssignment(
                    id=lab.get("id", ""),
                    title=lab.get("title", ""),
                    description=lab.get("description", ""),
                    due_date=lab.get("due_date", ""),
                    max_score=lab.get("max_score", 100),
                    status=lab.get("status", "available"),
                )
                for lab in labs_data
            ]
        except LMSClientError:
            raise
        except Exception as e:
            raise LMSClientNetworkError(f"Failed to fetch labs: {e}")

    def get_lab(self, lab_id: str) -> Optional[LabAssignment]:
        """Fetch a specific lab assignment."""
        try:
            data = self._request("GET", f"/api/labs/{lab_id}")
            return LabAssignment(
                id=data.get("id", ""),
                title=data.get("title", ""),
                description=data.get("description", ""),
                due_date=data.get("due_date", ""),
                max_score=data.get("max_score", 100),
                status=data.get("status", "available"),
            )
        except LMSClientError:
            return None
        except Exception as e:
            raise LMSClientNetworkError(f"Failed to fetch lab {lab_id}: {e}")

    def get_scores(self, student_id: str) -> list[Score]:
        """Fetch student's scores for all labs."""
        try:
            data = self._request("GET", f"/api/students/{student_id}/scores")
            scores_data = data.get("scores", []) if isinstance(data, dict) else data
            return [
                Score(
                    lab_id=score.get("lab_id", ""),
                    lab_title=score.get("lab_title", ""),
                    score=score.get("score"),
                    max_score=score.get("max_score", 100),
                    status=score.get("status", "not_starts"),
                    feedback=score.get("feedback"),
                )
                for score in scores_data
            ]
        except LMSClientError:
            raise
        except Exception as e:
            raise LMSClientNetworkError(f"Failed to fetch scores: {e}")

    def get_score(self, student_id: str, lab_id: str) -> Optional[Score]:
        """Fetch student's score for a specific lab."""
        try:
            data = self._request(
                "GET",
                f"/api/students/{student_id}/scores/{lab_id}",
            )
            return Score(
                lab_id=data.get("lab_id", ""),
                lab_title=data.get("lab_title", ""),
                score=data.get("score"),
                max_score=data.get("max_score", 100),
                status=data.get("status", "not_starts"),
                feedback=data.get("feedback"),
            )
        except LMSClientError:
            return None
        except Exception as e:
            raise LMSClientNetworkError(f"Failed to fetch score for lab {lab_id}: {e}")

    def health_check(self) -> bool:
        """Check if LMS API is available."""
        try:
            self._request("GET", "/api/health")
            return True
        except Exception:
            return False
