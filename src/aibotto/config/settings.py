"""
Configuration settings for the application.
"""

from dotenv import load_dotenv

from .env_loader import EnvLoader

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the AI Bot"""

    # Telegram Bot Configuration
    TELEGRAM_TOKEN: str = EnvLoader.get_str(
        "TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN_HERE"
    )

    # OpenAI Configuration
    OPENAI_API_KEY: str = EnvLoader.get_str(
        "OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE"
    )
    OPENAI_BASE_URL: str = EnvLoader.get_str(
        "OPENAI_BASE_URL", "https://api.openai.com/v1"
    )
    OPENAI_MODEL: str = EnvLoader.get_str("OPENAI_MODEL", "gpt-3.5-turbo")

    # Database Configuration
    DATABASE_PATH: str = EnvLoader.get_str("DATABASE_PATH", "conversations.db")

    # Security Configuration
    MAX_COMMAND_LENGTH: int = EnvLoader.get_int("MAX_COMMAND_LENGTH", 300000)
    ALLOWED_COMMANDS: list[str] = EnvLoader.get_list("ALLOWED_COMMANDS")
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
    MAX_HISTORY_LENGTH: int = EnvLoader.get_int("MAX_HISTORY_LENGTH", 20)
    THINKING_MESSAGE: str = EnvLoader.get_str("THINKING_MESSAGE", "🤔 Thinking...")

    # Web Search Configuration
    DDGS_TIMEOUT: int = EnvLoader.get_int("DDGS_TIMEOUT", 30)

    # LLM Configuration
    # Max tokens for LLM responses (None = no limit, lower values = faster responses)
    # For reasoning models, setting this to 1000-2000 can significantly improve speed
    LLM_MAX_TOKENS: int | None = EnvLoader.get_int("LLM_MAX_TOKENS", 0) or None

    # Tool Calling Configuration
    MAX_TOOL_ITERATIONS: int = EnvLoader.get_int("MAX_TOOL_ITERATIONS", 10)

    # Web Fetch Configuration
    WEB_FETCH_MAX_RETRIES: int = EnvLoader.get_int("WEB_FETCH_MAX_RETRIES", 3)
    WEB_FETCH_RETRY_DELAY: float = EnvLoader.get_float("WEB_FETCH_RETRY_DELAY", 1.0)
    WEB_FETCH_STRICT_CONTENT_TYPE: bool = EnvLoader.get_bool(
        "WEB_FETCH_STRICT_CONTENT_TYPE", True
    )

    # LLM Retry Configuration
    LLM_MAX_RETRIES: int = EnvLoader.get_int("LLM_MAX_RETRIES", 3)
    LLM_RETRY_DELAY: float = EnvLoader.get_float("LLM_RETRY_DELAY", 1.0)

    # Subagent Configuration
    SUBAGENT_MAX_CONCURRENT_TOOLS: int = EnvLoader.get_int(
        "SUBAGENT_MAX_CONCURRENT_TOOLS", 5
    )

    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration"""
        if cls.TELEGRAM_TOKEN == "YOUR_TELEGRAM_TOKEN_HERE":  # nosec: B105
            print("❌ TELEGRAM_TOKEN not set")
            return False

        if cls.OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE":
            print("❌ OPENAI_API_KEY not set")
            return False

        return True
