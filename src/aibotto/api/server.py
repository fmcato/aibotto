"""
FastAPI server for external trigger of LLM prompts.
"""

import logging
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..ai.agentic_orchestrator import AgenticOrchestrator
from ..bot.services.setup_service import BotSetupService
from .utils import TelegramMessageSender

logger = logging.getLogger(__name__)

app = FastAPI(title="AIBOTTO API", version="1.0.0")

bot_setup_service: BotSetupService | None = None
orchestrator: AgenticOrchestrator | None = None


def set_shared_objects(
    bot_service: BotSetupService, orch: AgenticOrchestrator
) -> None:
    """Set shared objects for API usage."""
    global bot_setup_service, orchestrator
    bot_setup_service = bot_service
    orchestrator = orch


class PromptRequest(BaseModel):
    chat_id: int | str
    prompt: str


async def _get_shared_objects() -> tuple[BotSetupService, AgenticOrchestrator]:
    """Get shared objects with validation."""
    if bot_setup_service is None or orchestrator is None:
        raise HTTPException(status_code=500, detail="API not properly initialized")
    return bot_setup_service, orchestrator


@app.post("/api/send")
async def send_prompt(request: PromptRequest) -> dict[str, Any]:
    """Send a prompt to the LLM and deliver response to Telegram chat."""
    setup_service, orch = await _get_shared_objects()
    application = setup_service.get_application()

    if not application:
        raise HTTPException(status_code=500, detail="Telegram bot application not available")

    logger.info(f"Processing API prompt for chat_id={request.chat_id}")

    response = await orch.process_prompt_stateless(request.prompt)

    message_sender = TelegramMessageSender(application)
    success = await message_sender.send_message(request.chat_id, response)

    if success:
        return {
            "status": "success",
            "message": f"Response sent to chat {request.chat_id}",
            "chat_id": request.chat_id,
        }
    else:
        raise HTTPException(status_code=500, detail=f"Failed to send response to chat {request.chat_id}")


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


def start_api_server(  # nosec: B104
    host: str = "0.0.0.0",
    port: int = 8001,
    bot_service: BotSetupService | None = None,
    orch: AgenticOrchestrator | None = None,
) -> None:
    """Start the API server in the current thread."""
    if bot_service and orch:
        set_shared_objects(bot_service, orch)

    logger.info(f"🌐 Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
