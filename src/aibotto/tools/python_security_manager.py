"""
Python security manager for code execution.
"""

import logging
from typing import Any

from ..config.python_security_config import PythonSecurityConfig
from .base_security_manager import BaseSecurityManager

logger = logging.getLogger(__name__)


class PythonSecurityManager(BaseSecurityManager):
    """Manager for Python code security operations."""

    def __init__(self, max_length: int | None = None) -> None:
        super().__init__(PythonSecurityConfig, max_length)

    # Override specific validation methods for Python code
    def _get_blocked_items(self) -> list[str]:
        """Get blocked patterns list."""
        return self.config.BLOCKED_PATTERNS
    
    def _get_allowed_items(self) -> list[str]:
        """Get allowed imports list."""
        return self.config.ALLOWED_IMPORTS
    
    def _get_max_length(self) -> int:
        """Get maximum Python code length."""
        return self.config.MAX_PYTHON_CODE_LENGTH

    async def validate_python_code(self, code: str) -> dict[str, Any]:
        """Validate Python code for security."""
        # Use the base validation method but with Python-specific checks
        return await self.validate_input(code)

    # Override specific validation methods for Python code
    async def _check_blocked_items(self, input_data: str) -> dict[str, Any] | None:
        """Check for blocked Python patterns."""
        code = input_data
        code_lower = code.lower()

        for pattern in self.blocked_items:
            if pattern in code_lower:
                logger.warning(
                    f"PYTHON BLOCKED PATTERNS CHECK: MATCHED - found '{pattern}' in code"
                )
                return self._create_blocked_result_dict(
                    f"Blocked Python pattern: {pattern}"
                )

        logger.debug("PYTHON BLOCKED PATTERNS CHECK: PASSED - no blocked patterns found")
        return None
    
    async def _check_allowed_items(self, input_data: str) -> dict[str, Any] | None:
        """Check for import restrictions."""
        if not self.allowed_items:
            # No import restrictions
            return None

        code = input_data
        # Find all import statements
        import_statements = self._extract_import_statements(code)

        for import_stmt in import_statements:
            # Check if the import is in the allowed list
            is_allowed = False
            for allowed_import in self.allowed_items:
                if allowed_import in import_stmt:
                    is_allowed = True
                    break

            if not is_allowed:
                logger.warning(
                    f"PYTHON IMPORT CHECK: BLOCKED - import '{import_stmt}' not in allowed list"
                )
                return self._create_blocked_result_dict(
                    f"Import not allowed: {import_stmt}"
                )

        return None

    def _extract_import_statements(self, code: str) -> list[str]:
        """Extract import statements from Python code."""
        import_statements = []
        lines = code.split("\n")

        for line in lines:
            line = line.strip()
            # Check for import statements
            if line.startswith("import ") or line.startswith("from "):
                # Extract the module name
                if line.startswith("import "):
                    module = line[7:].split()[0]  # Get the first word after 'import'
                else:  # from ... import ...
                    module = line[5:].split()[0]  # Get the first word after 'from'
                import_statements.append(module)

        return import_statements
