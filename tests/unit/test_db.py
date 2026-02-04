"""
Unit tests for DB module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.aibotto.db.operations import DatabaseOperations
from src.aibotto.config.settings import Config


class TestDatabaseOperations:
    """Test cases for DatabaseOperations class."""
    
    @pytest.fixture
    def db_ops(self):
        """Create a DatabaseOperations instance for testing."""
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value = MagicMock()
            db_ops = DatabaseOperations()
            return db_ops
    
    def test_init_database(self, db_ops):
        """Test database initialization."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        with patch('sqlite3.connect', return_value=mock_conn) as mock_connect:
            mock_conn.cursor.return_value = mock_cursor
            
            db_ops.init_database()
            
            mock_cursor.execute.assert_called_once()
            mock_conn.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_message(self, db_ops):
        """Test saving a message to database."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        with patch('sqlite3.connect', return_value=mock_conn) as mock_connect:
            mock_conn.cursor.return_value = mock_cursor
            
            await db_ops.save_message(123, 456, 1, "user", "Hello")
            
            mock_cursor.execute.assert_called_once()
            mock_conn.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self, db_ops):
        """Test retrieving conversation history."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # The database returns in reverse order (newest first), so we reverse it
        mock_cursor.fetchall.return_value = [
            ("assistant", "Hi there!"),
            ("user", "Hello")
        ]
        
        with patch('sqlite3.connect', return_value=mock_conn) as mock_connect:
            mock_conn.cursor.return_value = mock_cursor
            
            history = await db_ops.get_conversation_history(123, 456)
            
            assert len(history) == 2
            assert history[0]["role"] == "user"
            assert history[0]["content"] == "Hello"
            assert history[1]["role"] == "assistant"
            assert history[1]["content"] == "Hi there!"