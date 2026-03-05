"""
Python security configuration for the application.
"""

import os
from typing import Any

from .base_security_config import BaseSecurityConfig


class PythonSecurityConfig(BaseSecurityConfig):
    """Security configuration for Python code execution."""

    # Maximum Python code length allowed (raw code, not wrapped command)
    MAX_PYTHON_CODE_LENGTH: int = int(os.getenv("MAX_PYTHON_CODE_LENGTH", "60000"))

    # List of allowed imports (empty = no restrictions)
    ALLOWED_IMPORTS: list[str] = (
        os.getenv("PYTHON_ALLOWED_IMPORTS", "").split(",")
        if os.getenv("PYTHON_ALLOWED_IMPORTS")
        else []
    )

    # List of blocked Python patterns
    BLOCKED_PATTERNS: list[str] = [
        "exec(",
        "eval(",
        "subprocess.",
        "os.system(",
        "os.popen(",
        "commands.",
        "marshal.loads",
        "marshal.load",
        "pickle.loads",
        "pickle.load",
        "shutil.rmtree",
        "shutil.move",
        "shutil.copytree",
        "glob.glob",
        "fnmatch.filter",
        "tempfile.mktemp",
        "tempfile.NamedTemporaryFile",
        "socket.socket",
        "ssl.wrap_socket",
        "urllib.request.urlopen",
        "requests.get",
        "requests.post",
        "http.client.HTTPConnection",
        "ftplib.FTP",
        "smtplib.SMTP",
        "__import__('",
        "importlib.import_module",
        "importlib.util.spec_from_file_location",
        "importlib.util.spec_from_loader",
        "importlib.util.module_from_spec",
        "importlib.util.resolve_name",
        "importlib.util.find_spec",
        "importlib.util.module_for_loader",
        "importlib.util.set_package_wrapper",
        "importlib.util.set_loader_wrapper",
        "importlib.util.set_state_wrapper",
        "importlib.util.resolve_name",
        "importlib.util.find_spec",
        "importlib.util.module_from_spec",
        "importlib.util.spec_from_file_location",
        "importlib.util.spec_from_loader",
        "importlib.util.resolve_name",
    ]

    @classmethod
    def _apply_config(cls, config: dict[str, Any]) -> None:
        """Apply configuration values."""
        if "MAX_PYTHON_CODE_LENGTH" in config:
            cls.MAX_PYTHON_CODE_LENGTH = config["MAX_PYTHON_CODE_LENGTH"]
        if "ALLOWED_IMPORTS" in config:
            cls.ALLOWED_IMPORTS = config["ALLOWED_IMPORTS"]
        if "BLOCKED_PATTERNS" in config:
            cls.BLOCKED_PATTERNS = config["BLOCKED_PATTERNS"]

    @classmethod
    def _get_specific_summary(cls) -> dict[str, Any]:
        """Get security rules summary for specific subclass."""
        return {
            "max_python_code_length": cls.MAX_PYTHON_CODE_LENGTH,
            "allowed_imports_count": len(cls.ALLOWED_IMPORTS),
            "blocked_patterns_count": len(cls.BLOCKED_PATTERNS),
            "has_import_restrictions": bool(cls.ALLOWED_IMPORTS),
        }
