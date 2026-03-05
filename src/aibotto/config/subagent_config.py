"""Pydantic models for subagent configuration."""

import os
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class LLMProviderConfig(BaseModel):
    """Configuration for an LLM API provider.

    Attributes:
        api_key_env: Environment variable name containing the API key
        base_url: Base URL for the API endpoint
    """

    api_key_env: str = Field(
        ...,
        description="Environment variable name containing the API key",
    )
    base_url: str = Field(
        ...,
        description="Base URL for the API endpoint",
    )

    def get_api_key(self) -> str:
        """Get the API key from the environment variable.

        Returns:
            API key string

        Raises:
            ValueError: If the environment variable is not set
        """
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise ValueError(
                f"API key environment variable '{self.api_key_env}' is not set"
            )
        return api_key


class ProvidersConfig(BaseModel):
    """Configuration for LLM providers.

    Attributes:
        providers: Dictionary of provider name to provider config
    """

    providers: dict[str, LLMProviderConfig] = Field(
        default_factory=dict,
        description="Dictionary of provider name to provider config",
    )

    def get_provider(self, name: str) -> LLMProviderConfig:
        """Get a provider configuration by name.

        Args:
            name: Provider name

        Returns:
            LLMProviderConfig for the provider

        Raises:
            ValueError: If provider is not found
        """
        if name not in self.providers:
            available = ", ".join(self.providers.keys())
            raise ValueError(
                f"Provider '{name}' not found. Available providers: {available}"
            )
        return self.providers[name]


class SubAgentDefinition(BaseModel):
    """Definition of a subagent from configuration.

    Attributes:
        name: Unique identifier for the subagent
        disabled: If True, the subagent will not be registered
        description: Human-readable description
        provider: Name of the LLM provider to use
        model: Model identifier to use
        prompt_file: Path to the system prompt file (relative to config file)
        system_prompt: System prompt content (loaded from prompt_file)
        base_dir: Base directory for resolving prompt_file path
        tools: List of tool names available to this subagent
        max_iterations: Maximum agentic loop iterations
        temperature: Optional temperature setting
        max_tokens: Optional max tokens for responses
    """

    name: str = Field(
        ...,
        description="Unique identifier for the subagent",
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    disabled: bool = Field(
        default=False,
        description="If True, the subagent will not be registered",
    )
    description: str = Field(
        ...,
        description="Human-readable description",
        min_length=1,
    )
    provider: str = Field(
        ...,
        description="Name of the LLM provider to use",
    )
    model: str = Field(
        ...,
        description="Model identifier to use",
    )
    prompt_file: str = Field(
        ...,
        description="Path to the system prompt file (relative to config file)",
        min_length=1,
    )
    system_prompt: str = Field(
        default="",
        description="System prompt content (loaded from prompt_file)",
        exclude=True,
    )
    base_dir: Path | None = Field(
        None,
        description="Base directory for resolving prompt_file path",
        exclude=True,
    )
    tools: list[str] = Field(
        default_factory=list,
        description="List of tool names available to this subagent",
    )
    max_iterations: int = Field(
        default=5,
        description="Maximum agentic loop iterations",
        ge=1,
        le=20,
    )
    temperature: float | None = Field(
        default=None,
        description="Optional temperature setting",
        ge=0.0,
        le=2.0,
    )
    max_tokens: int | None = Field(
        default=None,
        description="Optional max tokens for responses",
        ge=1,
    )

    @field_validator("tools")
    @classmethod
    def validate_tools(cls, v: list[str]) -> list[str]:
        """Validate tool names are non-empty strings.

        Args:
            v: List of tool names

        Returns:
            Validated list of tool names

        Raises:
            ValueError: If any tool name is empty
        """
        for tool in v:
            if not tool or not tool.strip():
                raise ValueError("Tool names cannot be empty")
        return v


def resolve_env_vars(value: str) -> str:
    """Resolve environment variables in a string.

    Supports ${VAR_NAME} and ${VAR_NAME:-default} syntax.

    Args:
        value: String potentially containing env var references

    Returns:
        String with env vars resolved
    """
    pattern = r"\$\{([^}]+)\}"

    def replace_match(match: re.Match[str]) -> str:
        expr = match.group(1)
        if ":-" in expr:
            var_name, default = expr.split(":-", 1)
            return os.getenv(var_name, default)
        return os.getenv(expr, "")

    return re.sub(pattern, replace_match, value)


def resolve_config_env_vars(config: dict[str, Any]) -> dict[str, Any]:
    """Recursively resolve environment variables in config dict.

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with env vars resolved
    """
    result: dict[str, Any] = {}
    for key, value in config.items():
        if isinstance(value, str):
            result[key] = resolve_env_vars(value)
        elif isinstance(value, dict):
            result[key] = resolve_config_env_vars(value)
        elif isinstance(value, list):
            result[key] = [
                resolve_env_vars(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def load_prompt_file(prompt_file: str, base_dir: Path | None = None) -> str:
    """Load system prompt from file.

    Args:
        prompt_file: Path to the prompt file (relative to base_dir if provided)
        base_dir: Base directory for resolving relative paths

    Returns:
        Prompt content as string

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    if base_dir:
        prompt_path = base_dir / prompt_file
    else:
        prompt_path = Path(prompt_file)

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    content = prompt_path.read_text(encoding="utf-8")

    return content.strip()
