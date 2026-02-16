"""
Configuration settings for the application.
"""

import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the AI Bot"""

    # Telegram Bot Configuration
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN_HERE")

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # Database Configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "conversations.db")

    # Security Configuration
    MAX_COMMAND_LENGTH: int = int(os.getenv("MAX_COMMAND_LENGTH", "300000"))
    ALLOWED_COMMANDS: list[str] = (
        os.getenv("ALLOWED_COMMANDS", "").split(",")
        if os.getenv("ALLOWED_COMMANDS")
        else []
    )
    BLOCKED_COMMANDS: list[str] = [
        "rm -rf",
        "sudo",
        "dd",
        "mkfs",
        "fdisk",
        "format ",
        "format=",
        "format/",
        "shutdown",
        "reboot",
        "poweroff",
        "halt",
    ]

    # Bot Configuration
    MAX_HISTORY_LENGTH: int = int(os.getenv("MAX_HISTORY_LENGTH", "20"))
    THINKING_MESSAGE: str = os.getenv("THINKING_MESSAGE", "🤔 Thinking...")

    # Web Search Configuration
    # SEARXNG_BASE_URL: str = os.getenv("SEARXNG_BASE_URL", "http://localhost:8080")
    # SEARXNG_TIMEOUT: int = int(os.getenv("SEARXNG_TIMEOUT", "30"))
    DDGS_TIMEOUT: int = int(os.getenv("DDGS_TIMEOUT", "30"))

    # LLM Configuration
    # Max tokens for LLM responses (None = no limit, lower values = faster responses)
    # For reasoning models, setting this to 1000-2000 can significantly improve speed
    LLM_MAX_TOKENS: int | None = (
        int(os.getenv("LLM_MAX_TOKENS", "0")) or None
    )

    # Tool Calling Configuration
    MAX_TOOL_ITERATIONS: int = int(os.getenv("MAX_TOOL_ITERATIONS", "10"))

    # Web Fetch Configuration
    WEB_FETCH_MAX_RETRIES: int = int(os.getenv("WEB_FETCH_MAX_RETRIES", "3"))
    WEB_FETCH_RETRY_DELAY: float = float(os.getenv("WEB_FETCH_RETRY_DELAY", "1.0"))
    WEB_FETCH_STRICT_CONTENT_TYPE: bool = (
        os.getenv("WEB_FETCH_STRICT_CONTENT_TYPE", "true").lower() == "true"
    )

    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration"""
        if cls.TELEGRAM_TOKEN == "YOUR_TELEGRAM_TOKEN_HERE":
            print("❌ TELEGRAM_TOKEN not set")
            return False

        if cls.OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE":
            print("❌ OPENAI_API_KEY not set")
            return False

        return True

