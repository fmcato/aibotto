"""
Unit tests for enhanced CLI executor.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.aibotto.cli.enhanced_executor import EnhancedCLIExecutor, CommandSuggestion


class TestEnhancedCLIExecutor:
    """Test cases for EnhancedCLIExecutor class."""
    
    @pytest.fixture
    def executor(self):
        """Create an EnhancedCLIExecutor instance for testing."""
        with patch('src.aibotto.cli.enhanced_executor.CLIExecutor') as mock_cli:
            executor = EnhancedCLIExecutor()
            executor.execute_command = AsyncMock()
            return executor
    
    def test_command_suggestion_dataclass(self):
        """Test CommandSuggestion dataclass."""
        suggestion = CommandSuggestion("date", 0.9, "Get current time")
        
        assert suggestion.command == "date"
        assert suggestion.confidence == 0.9
        assert suggestion.reason == "Get current time"
    
    def test_build_command_suggestions(self):
        """Test command suggestions building."""
        executor = EnhancedCLIExecutor()
        
        # Test time suggestions
        time_suggestions = executor.command_suggestions.get("time")
        assert len(time_suggestions) == 3
        assert any(s.command == "date" for s in time_suggestions)
        
        # Test weather suggestions
        weather_suggestions = executor.command_suggestions.get("weather")
        assert len(weather_suggestions) == 2
        assert any("wttr.in" in s.command for s in weather_suggestions)
        
        # Test system suggestions
        system_suggestions = executor.command_suggestions.get("system")
        assert len(system_suggestions) == 3
        assert any(s.command == "uname -a" for s in system_suggestions)
    
    def test_suggest_command_time_query(self):
        """Test command suggestion for time queries."""
        executor = EnhancedCLIExecutor()
        
        suggestion = executor.suggest_command("what time is it")
        assert suggestion is not None
        assert suggestion.command == "date"
        assert suggestion.confidence == 0.9
        assert "Get current date and time" in suggestion.reason
    
    def test_suggest_command_weather_query(self):
        """Test command suggestion for weather queries."""
        executor = EnhancedCLIExecutor()
        
        suggestion = executor.suggest_command("what's the weather like")
        assert suggestion is not None
        assert "wttr.in" in suggestion.command
        assert suggestion.confidence == 0.9
    
    def test_suggest_command_system_query(self):
        """Test command suggestion for system queries."""
        executor = EnhancedCLIExecutor()
        
        suggestion = executor.suggest_command("tell me about the system")
        assert suggestion is not None
        assert suggestion.command == "uname -a"
        assert suggestion.confidence == 0.9
    
    def test_suggest_command_multiple_matches(self):
        """Test command suggestion with multiple matches."""
        executor = EnhancedCLIExecutor()
        
        # Query that matches multiple categories
        suggestion = executor.suggest_command("system memory information")
        assert suggestion is not None
        # Should pick the highest confidence match
        assert suggestion.confidence == 0.9
    
    def test_suggest_command_no_match(self):
        """Test command suggestion with no matches."""
        executor = EnhancedCLIExecutor()
        
        suggestion = executor.suggest_command("tell me a joke")
        assert suggestion is None
    
    @pytest.mark.asyncio
    async def test_execute_with_suggestion_success(self, executor):
        """Test execute_with_suggestion with successful execution."""
        executor.suggest_command = MagicMock(return_value=CommandSuggestion("date", 0.9, "Get time"))
        executor.execute_command = AsyncMock(return_value="Mon Feb 2 14:30:00 UTC 2026")
        
        result = await executor.execute_with_suggestion("what time is it")
        
        assert result == "Mon Feb 2 14:30:00 UTC 2026"
        executor.execute_command.assert_called_once_with("date")
    
    @pytest.mark.asyncio
    async def test_execute_with_suggestion_no_match(self, executor):
        """Test execute_with_suggestion with no command match."""
        executor.suggest_command = MagicMock(return_value=None)
        
        result = await executor.execute_with_suggestion("tell me a joke")
        
        assert "don't have access" in result
        executor.execute_command.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_fact_check_with_uncertainty(self, executor):
        """Test execute_fact_check with uncertain response."""
        executor.suggest_command = MagicMock(return_value=CommandSuggestion("date", 0.9, "Get time"))
        executor.execute_command = AsyncMock(return_value="Current time: 14:30")
        
        query = "what time is it"
        response = "it's probably around 2 PM"
        
        result = await executor.execute_fact_check(query, response)
        
        assert "Current time: 14:30" in result
        executor.execute_command.assert_called_once_with("date")
    
    @pytest.mark.asyncio
    async def test_execute_fact_check_no_uncertainty(self, executor):
        """Test execute_fact_check with certain response."""
        executor.suggest_command = MagicMock(return_value=None)
        
        query = "what time is it"
        response = "The current time is 2:30 PM"
        
        result = await executor.execute_fact_check(query, response)
        
        assert "No fact-check needed" in result
        executor.execute_command.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_fact_check_no_command_found(self, executor):
        """Test execute_fact_check when no command is found."""
        executor.suggest_command = MagicMock(return_value=None)
        
        query = "what time is it"
        response = "it's probably around 2 PM"
        
        result = await executor.execute_fact_check(query, response)
        
        assert "No fact-check needed" in result
        executor.execute_command.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_available_commands_info(self, executor):
        """Test get_available_commands_info method."""
        result = await executor.get_available_commands_info()
        
        assert "🤖" in result
        assert "factual information" in result
        assert "time" in result
        assert "Weather information" in result
        assert "system" in result
        assert "Just ask me" in result
    
    def test_command_suggestion_confidence_sorting(self):
        """Test that command suggestions are sorted by confidence."""
        executor = EnhancedCLIExecutor()
        
        # Test that highest confidence is returned
        suggestion = executor.suggest_command("what time is it")
        assert suggestion.confidence == 0.9
        
        # Test weather has same confidence as time (both are 0.9)
        time_suggestion = executor.suggest_command("what time is it")
        weather_suggestion = executor.suggest_command("what's the weather")
        assert time_suggestion.confidence == weather_suggestion.confidence == 0.9