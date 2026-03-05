"""Loader for subagent configuration from YAML files."""

import logging
from pathlib import Path
from typing import Any

import yaml  # type: ignore

from aibotto.ai.subagent.base import SubAgent as ConfigDrivenSubAgent
from aibotto.ai.subagent.registry import SubAgentRegistry
from aibotto.config.subagent_config import (
    LLMProviderConfig,
    ProvidersConfig,
    SubAgentDefinition,
    load_prompt_file,
    resolve_config_env_vars,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
DEFAULT_PROVIDERS_PATH = DEFAULT_CONFIG_DIR / "providers.yaml"
DEFAULT_SUBAGENTS_DIR = DEFAULT_CONFIG_DIR / "subagents"


def load_yaml_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load YAML configuration file.

    Args:
        config_path: Path to config file. If None, uses default path.

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    if not config_path:
        raise ValueError("config_path is required for load_yaml_config")

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        raw_config = yaml.safe_load(f)

    logger.info(f"Loaded raw config from {config_path}")

    return resolve_config_env_vars(raw_config)


def load_providers_config(
    providers_path: Path | None = None,
) -> ProvidersConfig:
    """Load and validate providers configuration.

    Args:
        providers_path: Path to providers config file.

    Returns:
        Validated ProvidersConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
        ValidationError: If validation fails
    """
    path = providers_path or DEFAULT_PROVIDERS_PATH

    if not path.exists():
        raise FileNotFoundError(f"Providers config file not found: {path}")

    raw_config = load_yaml_config(path)
    providers_data = raw_config.get("providers", {})

    providers = {}
    for name, provider_data in providers_data.items():
        providers[name] = LLMProviderConfig(**provider_data)

    config = ProvidersConfig(providers=providers)
    logger.info(f"Loaded {len(providers)} providers from {path}")
    return config


def discover_subagent_configs(
    subagents_dir: Path | None = None,
) -> dict[str, Path]:
    """Discover all subagent config directories.

    Scans the subagents directory for directories containing a config.yaml file.

    Args:
        subagents_dir: Path to subagents directory.

    Returns:
        Dictionary mapping subagent name to its config directory path

    Raises:
        FileNotFoundError: If subagents directory doesn't exist
    """
    dir_path = subagents_dir or DEFAULT_SUBAGENTS_DIR

    if not dir_path.exists():
        raise FileNotFoundError(f"Subagents directory not found: {dir_path}")

    subagent_configs = {}

    for entry in dir_path.iterdir():
        if not entry.is_dir():
            continue

        config_file = entry / "config.yaml"
        if not config_file.exists():
            logger.debug(f"Skipping {entry}: no config.yaml found")
            continue

        subagent_configs[entry.name] = entry

    logger.info(f"Discovered {len(subagent_configs)} subagent configs in {dir_path}")
    return subagent_configs


def load_subagent_definition(
    config_dir: Path,
) -> tuple[str, SubAgentDefinition]:
    """Load a single subagent definition from its config directory.

    Args:
        config_dir: Path to the subagent's config directory

    Returns:
        Tuple of (subagent_name, SubAgentDefinition)

    Raises:
        FileNotFoundError: If config files don't exist
        ValidationError: If validation fails
    """
    config_file = config_dir / "config.yaml"

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    raw_config = load_yaml_config(config_file)
    definition = SubAgentDefinition(**raw_config)

    return definition.name, definition


def load_prompt_for_subagent(
    definition: SubAgentDefinition,
    config_dir: Path,
) -> SubAgentDefinition:
    """Load system prompt for a subagent and update its definition.

    Args:
        definition: Subagent definition with prompt_file reference
        config_dir: Path to the subagent's config directory

    Returns:
        Updated SubAgentDefinition with system_prompt populated

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    prompt_content = load_prompt_file(definition.prompt_file, config_dir)

    updated_definition = definition.model_copy(
        update={"system_prompt": prompt_content, "base_dir": config_dir}
    )

    logger.debug(
        f"Loaded prompt for subagent '{definition.name}' from {definition.prompt_file}"
    )

    return updated_definition


def register_subagents_from_configs(
    providers_config: ProvidersConfig,
    subagent_defs: dict[str, tuple[SubAgentDefinition, LLMProviderConfig]],
) -> None:
    """Register all subagents from definitions and provider config.

    Args:
        providers_config: Configuration for LLM providers
        subagent_defs: Dictionary mapping name to (definition, provider) tuples

    Raises:
        ValueError: If provider not found for a subagent or environment variable not set
    """
    registered_count = 0
    skipped_count = 0

    for name, (definition, provider) in subagent_defs.items():
        if definition.disabled:
            logger.info(f"Skipping disabled subagent: '{name}'")
            skipped_count += 1
            continue

        provider_config = providers_config.get_provider(definition.provider)

        provider_config.get_api_key()

        SubAgentRegistry.register(name, ConfigDrivenSubAgent)
        registered_count += 1

        logger.info(
            f"Registered subagent '{name}' "
            f"(provider: {definition.provider}, model: {definition.model}, "
            f"tools: {definition.tools})"
        )

    SubAgentRegistry.register_factory_data(subagent_defs)

    logger.info(f"Registered {registered_count} subagents, skipped {skipped_count}")


def load_subagents_from_config(
    providers_path: Path | None = None,
    subagents_dir: Path | None = None,
) -> None:
    """Load, validate, and register all subagents from config directory.

    This is the main entry point for loading subagent configuration.

    Args:
        providers_path: Path to providers config file
        subagents_dir: Path to subagents directory

    Raises:
        FileNotFoundError: If config files or directories don't exist
        yaml.YAMLError: If YAML parsing fails
        ValidationError: If validation fails
        ValueError: If provider not found for a subagent
    """
    logger.info("Loading subagents from config directory")

    providers_config = load_providers_config(providers_path)

    subagent_dirs = discover_subagent_configs(subagents_dir)

    subagent_defs: dict[str, tuple[SubAgentDefinition, LLMProviderConfig]] = {}

    for name, config_dir in subagent_dirs.items():
        logger.debug(f"Processing subagent config: {name}")

        name_from_config, definition = load_subagent_definition(config_dir)

        if name_from_config != name:
            logger.warning(
                f"Config directory name '{name}' does not match config name "
                f"'{name_from_config}'. Using directory name."
            )

        definition = load_prompt_for_subagent(definition, config_dir)

        provider_config = providers_config.get_provider(definition.provider)

        subagent_defs[name] = (definition, provider_config)

    register_subagents_from_configs(providers_config, subagent_defs)

    logger.info(
        f"Subagent configuration loaded: {len(subagent_defs)} subagents processed"
    )
