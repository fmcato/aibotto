"""
Python security configuration for the application.
"""

import os


class PythonSecurityConfig:
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

    # Custom blocked patterns (for dynamic security rules)
    CUSTOM_BLOCKED_PATTERNS: list[str] = (
        os.getenv("PYTHON_CUSTOM_BLOCKED_PATTERNS", "").split(",")
        if os.getenv("PYTHON_CUSTOM_BLOCKED_PATTERNS")
        else []
    )

    # Security audit logging
    ENABLE_AUDIT_LOGGING: bool = (
        os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
    )

    @classmethod
    def reload_from_file(cls, config_file: str = "python_security_config.json") -> None:
        """Reload Python security configuration from file."""
        try:
            import json

            if os.path.exists(config_file):
                with open(config_file) as f:
                    config = json.load(f)

                # Update configuration values
                cls.MAX_PYTHON_CODE_LENGTH = config.get(
                    "MAX_PYTHON_CODE_LENGTH", cls.MAX_PYTHON_CODE_LENGTH
                )
                cls.ALLOWED_IMPORTS = config.get("ALLOWED_IMPORTS", cls.ALLOWED_IMPORTS)
                cls.BLOCKED_PATTERNS = config.get(
                    "BLOCKED_PATTERNS", cls.BLOCKED_PATTERNS
                )
                cls.CUSTOM_BLOCKED_PATTERNS = config.get(
                    "CUSTOM_BLOCKED_PATTERNS", cls.CUSTOM_BLOCKED_PATTERNS
                )
                cls.ENABLE_AUDIT_LOGGING = config.get(
                    "ENABLE_AUDIT_LOGGING", cls.ENABLE_AUDIT_LOGGING
                )

        except Exception as e:
            print(f"Warning: Could not reload Python security config from file: {e}")

    @classmethod
    def get_security_rules_summary(cls) -> dict[str, object]:
        """Get summary of current Python security rules."""
        return {
            "max_python_code_length": cls.MAX_PYTHON_CODE_LENGTH,
            "allowed_imports_count": len(cls.ALLOWED_IMPORTS),
            "blocked_patterns_count": len(cls.BLOCKED_PATTERNS),
            "custom_blocked_patterns_count": len(cls.CUSTOM_BLOCKED_PATTERNS),
            "audit_logging_enabled": cls.ENABLE_AUDIT_LOGGING,
            "has_import_restrictions": bool(cls.ALLOWED_IMPORTS),
        }
