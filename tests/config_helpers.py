"""Helper functions for managing config in tests."""

from src.aibotto.config.settings import Config


def backup_config() -> dict[str, object]:
    """Backup all non-private config attributes."""
    original_config = {}
    for key in dir(Config):
        if not key.startswith('_'):
            original_config[key] = getattr(Config, key)
    return original_config


def restore_config(original_config: dict[str, object]) -> None:
    """Restore config from backup."""
    for key, value in original_config.items():
        setattr(Config, key, value)