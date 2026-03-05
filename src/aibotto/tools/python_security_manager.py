"""
Python security manager for code execution.
"""

import logging

from ..config.python_security_config import PythonSecurityConfig

logger = logging.getLogger(__name__)


class PythonSecurityManager:
    """Manager for Python code security operations."""

    def __init__(self) -> None:
        self.config = PythonSecurityConfig()
        self.blocked_patterns = self.config.BLOCKED_PATTERNS
        self.allowed_imports = self.config.ALLOWED_IMPORTS
        self.custom_blocked_patterns = self.config.CUSTOM_BLOCKED_PATTERNS
        self.max_python_code_length = self.config.MAX_PYTHON_CODE_LENGTH
        self.enable_audit_logging = self.config.ENABLE_AUDIT_LOGGING

    async def validate_python_code(self, code: str) -> dict[str, object]:
        """Validate Python code for security."""
        result = {"allowed": False, "message": ""}

        logger.debug(
            f"PYTHON SECURITY CHECK: Starting validation for code (length: {len(code)}, limit: {self.max_python_code_length})"
        )
        logger.debug(f"PYTHON SECURITY CHECK: Code preview: {code[:100]}...")

        # Check Python code length (raw code, not wrapped command)
        length_check = await self._check_python_code_length(code)
        if length_check:
            logger.warning(
                f"PYTHON SECURITY CHECK: Blocked by length check - {length_check['message']}"
            )
            return length_check

        # Check for blocked patterns (exec, subprocess, etc.)
        pattern_check = await self._check_blocked_patterns(code)
        if pattern_check:
            logger.warning(
                f"PYTHON SECURITY CHECK: Blocked by pattern check - {pattern_check['message']}"
            )
            return pattern_check

        # Check import restrictions
        import_check = await self._check_import_restrictions(code)
        if import_check:
            logger.warning(
                f"PYTHON SECURITY CHECK: Blocked by import check - {import_check['message']}"
            )
            return import_check

        # Check custom blocked patterns
        custom_pattern_check = await self._check_custom_patterns(code)
        if custom_pattern_check:
            logger.warning(
                f"PYTHON SECURITY CHECK: Blocked by custom pattern check - {custom_pattern_check['message']}"
            )
            return custom_pattern_check

        # Python code is allowed
        logger.info("PYTHON SECURITY CHECK: Code PASSED all security checks")
        if self.enable_audit_logging:
            logger.info(f"Python Code allowed: {code[:50]}...")

        result["allowed"] = True
        return result

    async def _check_python_code_length(self, code: str) -> dict[str, object] | None:
        """Check if Python code length exceeds maximum."""
        logger.debug(
            f"PYTHON LENGTH CHECK: Code length={len(code)}, max={self.max_python_code_length}"
        )
        if len(code) > self.max_python_code_length:
            message = f"Error: Python code too long (max {self.max_python_code_length} characters)"
            if self.enable_audit_logging:
                logger.warning(f"Python Code blocked for length: {code[:50]}...")
            return self._create_blocked_result_dict(message)
        logger.debug("PYTHON LENGTH CHECK: PASSED")
        return None

    async def _check_blocked_patterns(self, code: str) -> dict[str, object] | None:
        """Check for blocked Python patterns."""
        code_lower = code.lower()

        logger.debug(
            f"PYTHON BLOCKED PATTERNS CHECK: Checking {len(self.blocked_patterns)} blocked patterns"
        )

        for pattern in self.blocked_patterns:
            if pattern in code_lower:
                logger.warning(
                    f"PYTHON BLOCKED PATTERNS CHECK: MATCHED - found '{pattern}' in code"
                )
                return self._create_blocked_result(
                    f"Blocked Python pattern: {pattern}", pattern
                )

        logger.debug(
            "PYTHON BLOCKED PATTERNS CHECK: PASSED - no blocked patterns found"
        )
        return None

    async def _check_import_restrictions(self, code: str) -> dict[str, object] | None:
        """Check for import restrictions."""
        if not self.allowed_imports:
            # No import restrictions
            return None

        # Find all import statements
        import_statements = self._extract_import_statements(code)

        for import_stmt in import_statements:
            # Check if the import is in the allowed list
            is_allowed = False
            for allowed_import in self.allowed_imports:
                if allowed_import in import_stmt:
                    is_allowed = True
                    break

            if not is_allowed:
                logger.warning(
                    f"PYTHON IMPORT CHECK: BLOCKED - import '{import_stmt}' not in allowed list"
                )
                return self._create_blocked_result(
                    f"Import not allowed: {import_stmt}", "import_restriction"
                )

        return None

    async def _check_custom_patterns(self, code: str) -> dict[str, object] | None:
        """Check for custom blocked patterns."""
        code_lower = code.lower()

        for pattern in self.custom_blocked_patterns:
            if pattern and pattern in code_lower:
                message = (
                    "Error: Python code matches blocked pattern for security reasons"
                )
                if self.enable_audit_logging:
                    logger.warning(f"Python Blocked custom pattern '{pattern}': {code}")
                return self._create_blocked_result_dict(message)

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

    def _create_blocked_result_dict(self, message: str) -> dict[str, object]:
        """Create a standard blocked result dict."""
        return {"allowed": False, "message": message}

    def _create_blocked_result(self, message: str, danger: str) -> dict[str, object]:
        """Create a blocked result dict."""
        return {"allowed": False, "message": message}
