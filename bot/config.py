"""
Configuration management for Telegram bot.

Loads environment variables from .env.bot.secret with fallback to .env.bot.example.
Simple implementation without pydantic for minimal dependencies.
"""

import os
from pathlib import Path
from typing import Optional


def find_env_file() -> Optional[Path]:
    """
    Find the environment file to load.

    Priority:
    1. .env.bot.secret (production secrets)
    2. .env.bot.example (example/fallback)
    """
    bot_dir = Path(__file__).parent
    secret_file = bot_dir / ".env.bot.secret"
    example_file = bot_dir / ".env.bot.example"

    if secret_file.exists():
        return secret_file
    if example_file.exists():
        return example_file
    return None


class BotSettings:
    """Bot configuration settings."""

    def __init__(self, env_file: Optional[Path] = None) -> None:
        """
        Initialize settings from environment file or environment variables.

        Args:
            env_file: Path to .env file to load
        """
        # Telegram Bot Token
        self.telegram_bot_token = os.getenv("BOT_TOKEN", "")

        # LMS Backend API
        self.lms_api_url = os.getenv("LMS_API_BASE_URL", "http://localhost:8000")
        self.lms_api_key = os.getenv("LMS_API_KEY", "")

        # LLM API (for intent recognition)
        self.llm_api_url = os.getenv("LLM_API_BASE_URL", "http://localhost:11434")
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        self.llm_model = os.getenv("LLM_API_MODEL", "coder-model")

        # Bot settings
        self.bot_name = "SE Toolkit Bot"
        self.debug_mode = False

        # Load from file if provided (overrides env vars)
        if env_file and env_file.exists():
            self._load_from_file(env_file)

    def _load_from_file(self, env_file: Path) -> None:
        """Load settings from .env file."""
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip().lower()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith("<") and value.endswith(">"):
                    value = ""
                
                if key == "bot_token":
                    self.telegram_bot_token = value
                elif key == "lms_api_base_url":
                    self.lms_api_url = value
                elif key == "lms_api_key":
                    self.lms_api_key = value
                elif key == "llm_api_base_url":
                    self.llm_api_url = value
                elif key == "llm_api_key":
                    self.llm_api_key = value
                elif key == "llm_api_model":
                    self.llm_model = value

    @property
    def is_configured(self) -> bool:
        """Check if bot has required configuration to run."""
        return bool(self.telegram_bot_token)


# Global settings instance
_settings: Optional[BotSettings] = None


def get_settings() -> BotSettings:
    """
    Get or create global settings instance.

    Returns:
        BotSettings: Global configuration object
    """
    global _settings
    if _settings is None:
        env_file = find_env_file()
        _settings = BotSettings(env_file)
    return _settings


def reload_settings() -> BotSettings:
    """
    Reload settings from environment file.

    Returns:
        BotSettings: Fresh configuration object
    """
    global _settings
    env_file = find_env_file()
    _settings = BotSettings(env_file)
    return _settings
