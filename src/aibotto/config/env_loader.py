"""
Unified environment variable loader with type conversion.

Consolidates repeated environment variable loading patterns across the codebase.
"""

import os


class EnvLoader:
    """Unified environment variable loader with type conversion."""

    @staticmethod
    def get_str(key: str, default: str = "", required: bool = False) -> str:
        """Load string environment variable.

        Args:
            key: Environment variable name
            default: Default value if not set
            required: Raise error if not set

        Returns:
            String value or default

        Raises:
            ValueError: If required and not set
        """
        value = os.getenv(key, default)
        if required and not value:
            raise ValueError(f"Required environment variable '{key}' is not set")
        return value

    @staticmethod
    def get_int(key: str, default: int = 0, required: bool = False) -> int:
        """Load integer environment variable.

        Args:
            key: Environment variable name
            default: Default value if not set or invalid
            required: Raise error if not set

        Returns:
            Integer value or default

        Raises:
            ValueError: If required and invalid or not set
        """
        value = os.getenv(key, str(default))
        try:
            return int(value)
        except ValueError:
            if required:
                raise ValueError(f"Invalid integer value for '{key}': {value}")
            return default

    @staticmethod
    def get_float(key: str, default: float = 0.0, required: bool = False) -> float:
        """Load float environment variable.

        Args:
            key: Environment variable name
            default: Default value if not set or invalid
            required: Raise error if not set

        Returns:
            Float value or default

        Raises:
            ValueError: If required and invalid or not set
        """
        value = os.getenv(key, str(default))
        try:
            return float(value)
        except ValueError:
            if required:
                raise ValueError(f"Invalid float value for '{key}': {value}")
            return default

    @staticmethod
    def get_bool(key: str, default: bool = False, required: bool = False) -> bool:
        """Load boolean environment variable.

        Args:
            key: Environment variable name
            default: Default value if not set or invalid
            required: Raise error if not set

        Returns:
            Boolean value or default

        Raises:
            ValueError: If required and invalid or not set
        """
        value = os.getenv(key, str(default)).lower()
        if value in ("true", "1", "yes", "on"):
            return True
        elif value in ("false", "0", "no", "off"):
            return False
        elif required:
            raise ValueError(f"Invalid boolean value for '{key}': {value}")
        return default

    @staticmethod
    def get_list(
        key: str,
        separator: str = ",",
        default: list[str] | None = None,
        filter_empty: bool = True,
        required: bool = False,
    ) -> list[str]:
        """Load list environment variable.

        Args:
            key: Environment variable name
            separator: String separator for list items
            default: Default value if not set
            filter_empty: Remove empty strings from result
            required: Raise error if not set

        Returns:
            List of strings or default

        Raises:
            ValueError: If required and not set
        """
        raw_value = os.getenv(key)
        if not raw_value:
            if required:
                raise ValueError(f"Required environment variable '{key}' is not set")
            return default or []

        items = raw_value.split(separator)
        if filter_empty:
            items = [item.strip() for item in items if item.strip()]
        else:
            items = [item.strip() for item in items]

        return items
