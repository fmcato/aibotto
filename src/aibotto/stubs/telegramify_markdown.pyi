from typing import Any

try:
    from telegramify_markdown import telegramify
except ImportError:
    # Create a stub for telegramify_markdown when not available
    class _TelegramifyMarkdown:
        def __init__(self) -> None:
            pass
        async def telegramify(self, text: str) -> list[Any]:
            return [text]
    telegramify = _TelegramifyMarkdown().telegramify
