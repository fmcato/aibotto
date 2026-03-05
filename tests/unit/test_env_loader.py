"""
Tests for unified environment variable loader.
"""

import os
import pytest

from src.aibotto.config.env_loader import EnvLoader


class TestEnvLoader:
    """Test environment variable loading functionality."""

    def test_get_str_with_value(self):
        """Test loading string environment variable."""
        os.environ["TEST_STRING"] = "hello"
        result = EnvLoader.get_str("TEST_STRING")
        assert result == "hello"
        del os.environ["TEST_STRING"]

    def test_get_str_with_default(self):
        """Test loading string with default value."""
        result = EnvLoader.get_str("NONEXISTENT_VAR", "default_value")
        assert result == "default_value"

    def test_get_str_required(self):
        """Test required string variable raises error when missing."""
        with pytest.raises(ValueError, match="Required environment variable"):
            EnvLoader.get_str("MISSING_REQUIRED_VAR", required=True)

    def test_get_int_with_value(self):
        """Test loading integer environment variable."""
        os.environ["TEST_INT"] = "42"
        result = EnvLoader.get_int("TEST_INT")
        assert result == 42
        del os.environ["TEST_INT"]

    def test_get_int_with_default(self):
        """Test loading integer with default value."""
        result = EnvLoader.get_int("NONEXISTENT_INT", 100)
        assert result == 100

    def test_get_int_invalid_value(self):
        """Test invalid integer value returns default."""
        os.environ["INVALID_INT"] = "not_a_number"
        result = EnvLoader.get_int("INVALID_INT", 42)
        assert result == 42
        del os.environ["INVALID_INT"]

    def test_get_int_required_invalid(self):
        """Test required integer raises error for invalid value."""
        os.environ["REQUIRED_INVALID_INT"] = "not_a_number"
        with pytest.raises(ValueError, match="Invalid integer value"):
            EnvLoader.get_int("REQUIRED_INVALID_INT", required=True)
        del os.environ["REQUIRED_INVALID_INT"]

    def test_get_float_with_value(self):
        """Test loading float environment variable."""
        os.environ["TEST_FLOAT"] = "3.14"
        result = EnvLoader.get_float("TEST_FLOAT")
        assert result == 3.14
        del os.environ["TEST_FLOAT"]

    def test_get_float_with_default(self):
        """Test loading float with default value."""
        result = EnvLoader.get_float("NONEXISTENT_FLOAT", 2.5)
        assert result == 2.5

    def test_get_float_invalid_value(self):
        """Test invalid float value returns default."""
        os.environ["INVALID_FLOAT"] = "not_a_float"
        result = EnvLoader.get_float("INVALID_FLOAT", 1.0)
        assert result == 1.0
        del os.environ["INVALID_FLOAT"]

    def test_get_bool_true_values(self):
        """Test boolean true values."""
        for value in ["true", "1", "yes", "on"]:
            os.environ["TEST_BOOL"] = value
            result = EnvLoader.get_bool("TEST_BOOL")
            assert result is True
        del os.environ["TEST_BOOL"]

    def test_get_bool_false_values(self):
        """Test boolean false values."""
        for value in ["false", "0", "no", "off"]:
            os.environ["TEST_BOOL"] = value
            result = EnvLoader.get_bool("TEST_BOOL")
            assert result is False
        del os.environ["TEST_BOOL"]

    def test_get_bool_with_default(self):
        """Test loading boolean with default value."""
        result = EnvLoader.get_bool("NONEXISTENT_BOOL", True)
        assert result is True

    def test_get_bool_invalid_value(self):
        """Test invalid boolean value returns default."""
        os.environ["INVALID_BOOL"] = "not_a_bool"
        result = EnvLoader.get_bool("INVALID_BOOL", False)
        assert result is False
        del os.environ["INVALID_BOOL"]

    def test_get_bool_required_invalid(self):
        """Test required boolean raises error for invalid value."""
        os.environ["REQUIRED_INVALID_BOOL"] = "not_a_bool"
        with pytest.raises(ValueError, match="Invalid boolean value"):
            EnvLoader.get_bool("REQUIRED_INVALID_BOOL", required=True)
        del os.environ["REQUIRED_INVALID_BOOL"]

    def test_get_list_with_value(self):
        """Test loading list environment variable."""
        os.environ["TEST_LIST"] = "item1,item2,item3"
        result = EnvLoader.get_list("TEST_LIST")
        assert result == ["item1", "item2", "item3"]
        del os.environ["TEST_LIST"]

    def test_get_list_with_custom_separator(self):
        """Test loading list with custom separator."""
        os.environ["TEST_LIST"] = "item1;item2;item3"
        result = EnvLoader.get_list("TEST_LIST", separator=";")
        assert result == ["item1", "item2", "item3"]
        del os.environ["TEST_LIST"]

    def test_get_list_with_spaces(self):
        """Test loading list with spaces and commas."""
        os.environ["TEST_LIST"] = "item1 , item2 , item3"
        result = EnvLoader.get_list("TEST_LIST")
        assert result == ["item1", "item2", "item3"]
        del os.environ["TEST_LIST"]

    def test_get_list_filter_empty(self):
        """Test loading list filters empty items."""
        os.environ["TEST_LIST"] = "item1,,item2,,item3"
        result = EnvLoader.get_list("TEST_LIST")
        assert result == ["item1", "item2", "item3"]
        del os.environ["TEST_LIST"]

    def test_get_list_keep_empty(self):
        """Test loading list keeps empty items when disabled."""
        os.environ["TEST_LIST"] = "item1,,item2"
        result = EnvLoader.get_list("TEST_LIST", filter_empty=False)
        assert result == ["item1", "", "item2"]
        del os.environ["TEST_LIST"]

    def test_get_list_empty_var_with_default(self):
        """Test loading list returns default when variable is empty."""
        result = EnvLoader.get_list("NONEXISTENT_LIST", default=["default1", "default2"])
        assert result == ["default1", "default2"]

    def test_get_list_empty_var_no_default(self):
        """Test loading list returns empty list when variable is empty."""
        result = EnvLoader.get_list("NONEXISTENT_LIST")
        assert result == []

    def test_get_list_required_missing(self):
        """Test required list raises error when missing."""
        with pytest.raises(ValueError, match="Required environment variable"):
            EnvLoader.get_list("MISSING_REQUIRED_LIST", required=True)

    def test_get_list_empty_string_required(self):
        """Test required list raises error when empty string."""
        os.environ["EMPTY_LIST"] = ""
        with pytest.raises(ValueError, match="Required environment variable"):
            EnvLoader.get_list("EMPTY_LIST", required=True)
        del os.environ["EMPTY_LIST"]