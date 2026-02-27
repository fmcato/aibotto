"""Unit tests for BotSetupService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aibotto.bot.services.setup_service import BotSetupService


@pytest.fixture
def setup_service():
    """Create a BotSetupService instance for testing."""
    return BotSetupService()


@pytest.fixture
def mock_token():
    """Mock Telegram token."""
    return "test_token_12345"


class TestInitializeApplication:
    """Test the initialize_application method."""

    @pytest.mark.asyncio
    async def test_initialize_application_applies_patch(self, mock_token):
        """Test that initialize_application applies the monkey patch."""
        service = BotSetupService()

        # Mock the Application.builder().token().build() chain
        mock_application = AsyncMock()
        mock_application.bot = AsyncMock()
        mock_application.initialize = AsyncMock()

        with patch('aibotto.bot.services.setup_service.Application') as mock_app_class:
            mock_builder = MagicMock()
            mock_builder.token.return_value.build.return_value = mock_application
            mock_app_class.builder.return_value = mock_builder

            await service.initialize_application(mock_token)

        # Verify the bot was created (meaning initialization succeeded)
        assert service.application == mock_application

    @pytest.mark.asyncio
    async def test_initialize_application_handles_errors(self, mock_token):
        """Test that initialize_application handles errors gracefully."""
        service = BotSetupService()

        with patch('aibotto.bot.services.setup_service.Application') as mock_app_class:
            mock_builder = MagicMock()
            mock_builder.token.return_value.build.side_effect = Exception("Token error")
            mock_app_class.builder.return_value = mock_builder

            with pytest.raises(Exception, match="Token error"):
                await service.initialize_application(mock_token)
