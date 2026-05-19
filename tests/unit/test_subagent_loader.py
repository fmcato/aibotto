"""
Unit tests for subagent loader module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from aibotto.ai.subagent.loader import (
    discover_subagent_configs,
    load_prompt_for_subagent,
    load_providers_config,
    load_subagent_definition,
    load_subagents_from_config,
    load_yaml_config,
    register_subagents_from_configs,
)
from aibotto.ai.subagent.registry import SubAgentRegistry
from aibotto.config.subagent_config import (
    LLMProviderConfig,
    ProvidersConfig,
    SubAgentDefinition,
)


@pytest.fixture
def temp_config_dir():
    """Create temporary directory with test config files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)

        providers_config = {
            "providers": {
                "openai": {
                    "base_url": "https://api.openai.com/v1",
                    "api_key_env": "TEST_OPENAI_API_KEY",
                }
            }
        }
        providers_file = config_dir / "providers.yaml"
        with open(providers_file, "w") as f:
            yaml.dump(providers_config, f)

        subagent_dir = config_dir / "subagents" / "test_agent"
        subagent_dir.mkdir(parents=True)

        subagent_config = {
            "name": "test_agent",
            "description": "A test subagent",
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "max_iterations": 3,
            "tools": ["search_web"],
            "prompt_file": "prompt.md",
            "disabled": False,
        }
        config_file = subagent_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(subagent_config, f)

        prompt_file = subagent_dir / "prompt.md"
        prompt_file.write_text("You are a test agent.")

        yield config_dir


@pytest.fixture
def reset_registry():
    """Reset the subagent registry before and after tests."""
    SubAgentRegistry._subagents.clear()
    SubAgentRegistry._factory_configs.clear()
    yield
    SubAgentRegistry._subagents.clear()
    SubAgentRegistry._factory_configs.clear()


@pytest.fixture
def mock_api_key():
    """Set test API key environment variable."""
    original = os.environ.get("TEST_OPENAI_API_KEY")
    os.environ["TEST_OPENAI_API_KEY"] = "test_key_12345"
    yield
    if original is None:
        os.environ.pop("TEST_OPENAI_API_KEY", None)
    else:
        os.environ["TEST_OPENAI_API_KEY"] = original


class TestLoadYamlConfig:
    """Test YAML config loading."""

    def test_load_yaml_config_success(self, temp_config_dir):
        """Test successful YAML config loading."""
        providers_file = temp_config_dir / "providers.yaml"
        result = load_yaml_config(providers_file)

        assert "providers" in result
        assert "openai" in result["providers"]

    def test_load_yaml_config_file_not_found(self):
        """Test FileNotFoundError for missing config."""
        with pytest.raises(FileNotFoundError):
            load_yaml_config(Path("/nonexistent/config.yaml"))

    def test_load_yaml_config_none_path(self):
        """Test ValueError for None config path."""
        with pytest.raises(ValueError, match="config_path is required"):
            load_yaml_config(None)


class TestLoadProvidersConfig:
    """Test providers config loading."""

    def test_load_providers_config_success(self, temp_config_dir):
        """Test successful providers config loading."""
        providers_file = temp_config_dir / "providers.yaml"
        result = load_providers_config(providers_file)

        assert isinstance(result, ProvidersConfig)
        assert "openai" in result.providers

    def test_load_providers_config_file_not_found(self):
        """Test FileNotFoundError for missing providers config."""
        with pytest.raises(FileNotFoundError):
            load_providers_config(Path("/nonexistent/providers.yaml"))


class TestDiscoverSubagentConfigs:
    """Test subagent config discovery."""

    def test_discover_subagent_configs_success(self, temp_config_dir):
        """Test successful discovery of subagent configs."""
        subagents_dir = temp_config_dir / "subagents"
        result = discover_subagent_configs(subagents_dir)

        assert "test_agent" in result
        assert result["test_agent"].is_dir()

    def test_discover_subagent_configs_dir_not_found(self):
        """Test FileNotFoundError for missing subagents directory."""
        with pytest.raises(FileNotFoundError):
            discover_subagent_configs(Path("/nonexistent/subagents"))

    def test_discover_skips_dirs_without_config(self, temp_config_dir):
        """Test that directories without config.yaml are skipped."""
        subagents_dir = temp_config_dir / "subagents"
        empty_dir = subagents_dir / "empty_agent"
        empty_dir.mkdir()

        result = discover_subagent_configs(subagents_dir)

        assert "empty_agent" not in result
        assert "test_agent" in result


class TestLoadSubagentDefinition:
    """Test subagent definition loading."""

    def test_load_subagent_definition_success(self, temp_config_dir):
        """Test successful subagent definition loading."""
        config_dir = temp_config_dir / "subagents" / "test_agent"
        name, definition = load_subagent_definition(config_dir)

        assert name == "test_agent"
        assert isinstance(definition, SubAgentDefinition)
        assert definition.name == "test_agent"
        assert definition.provider == "openai"
        assert definition.max_iterations == 3

    def test_load_subagent_definition_config_not_found(self):
        """Test FileNotFoundError for missing config."""
        with pytest.raises(FileNotFoundError):
            load_subagent_definition(Path("/nonexistent/agent"))


class TestLoadPromptForSubagent:
    """Test prompt loading for subagents."""

    def test_load_prompt_for_subagent_success(self, temp_config_dir):
        """Test successful prompt loading."""
        config_dir = temp_config_dir / "subagents" / "test_agent"
        _, definition = load_subagent_definition(config_dir)
        updated = load_prompt_for_subagent(definition, config_dir)

        assert updated.system_prompt == "You are a test agent."
        assert updated.base_dir == config_dir


class TestRegisterSubagentsFromConfigs:
    """Test subagent registration."""

    def test_register_subagents_success(self, reset_registry, mock_api_key):
        """Test successful subagent registration."""
        provider = LLMProviderConfig(
            base_url="https://api.openai.com/v1",
            api_key_env="TEST_OPENAI_API_KEY",
        )
        definition = SubAgentDefinition(
            name="test_agent",
            description="Test agent",
            provider="openai",
            model="gpt-3.5-turbo",
            max_iterations=3,
            tools=["search_web"],
            prompt_file="prompt.md",
            system_prompt="You are a test agent.",
            disabled=False,
        )

        subagent_defs = {"test_agent": (definition, provider)}
        providers_config = ProvidersConfig(providers={"openai": provider})

        register_subagents_from_configs(providers_config, subagent_defs)

        assert SubAgentRegistry.get("test_agent") is not None

    def test_register_skips_disabled_subagents(self, reset_registry, mock_api_key):
        """Test that disabled subagents are skipped."""
        provider = LLMProviderConfig(
            base_url="https://api.openai.com/v1",
            api_key_env="TEST_OPENAI_API_KEY",
        )
        definition = SubAgentDefinition(
            name="disabled_agent",
            description="Disabled agent",
            provider="openai",
            model="gpt-3.5-turbo",
            max_iterations=3,
            tools=["search_web"],
            prompt_file="prompt.md",
            system_prompt="You are disabled.",
            disabled=True,
        )

        subagent_defs = {"disabled_agent": (definition, provider)}
        providers_config = ProvidersConfig(providers={"openai": provider})

        register_subagents_from_configs(providers_config, subagent_defs)

        assert SubAgentRegistry.get("disabled_agent") is None


class TestLoadSubagentsFromConfig:
    """Test full subagent loading pipeline."""

    def test_load_subagents_from_config_success(
        self, temp_config_dir, reset_registry, mock_api_key
    ):
        """Test successful full pipeline loading."""
        providers_file = temp_config_dir / "providers.yaml"
        subagents_dir = temp_config_dir / "subagents"

        load_subagents_from_config(providers_file, subagents_dir)

        assert SubAgentRegistry.get("test_agent") is not None
