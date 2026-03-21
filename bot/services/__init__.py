"""
Service clients for external APIs.

This module contains clients for communicating with external services:
- LMS backend for student data, labs, and scores
- LLM API for intent recognition
"""

from .lms_client import LMSClient
from .llm_client import LLMClient

__all__ = [
    "LMSClient",
    "LLMClient",
]
