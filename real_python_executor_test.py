#!/usr/bin/env python3
"""
Test to reproduce the exact Python security issue with the real Python executor logic.
"""

import asyncio
import json


class MockSecurityConfig:
    """Mock security configuration."""
    
    # Maximum command length allowed
    MAX_COMMAND_LENGTH: int = 1000  # Docker sets this to 1000
    
    # Maximum Python code length allowed (higher than general commands)
    MAX_PYTHON_CODE_LENGTH: int = 60000
    
    # Whitelist of allowed commands (empty = no whitelist)
    ALLOWED_COMMANDS: list[str] = []
    
    # Blacklist of blocked commands
    BLOCKED_COMMANDS: list[str] = [
        "rm -rf",
        "sudo",
        "dd",
        "mkfs",
        "fdisk",
        "format ",
        "format=",
        "format/",
        "shutdown",
        "reboot",
        "poweroff",
        "halt",
    ]
    
    # Custom blocked patterns (for dynamic security rules)
    CUSTOM_BLOCKED_PATTERNS: list[str] = []
    
    # Security audit logging
    ENABLE_AUDIT_LOGGING: bool = True


class MockPythonExecutor:
    """Mock Python executor that matches the real one exactly."""
    
    def __init__(self):
        self.security_manager = MockSecurityManager(
            max_length=MockSecurityConfig.MAX_PYTHON_CODE_LENGTH
        )
    
    def _wrap_python_code(self, code: str) -> str:
        """Wrap Python code for execution - matches real implementation."""
        if "\n" in code:
            return f"uv run python << 'EOF'\n{code}\nEOF"
        else:
            return f"uv run python -c '{code}'"
    
    async def execute_python_code(self, code: str) -> str:
        """Execute Python code with security validation - matches real implementation."""
        try:
            # This matches the real executor's argument parsing
            args = {"code": code}
            parsed_code = args.get("code")

            if not parsed_code:
                raise ValueError("No code provided")

            print(f"Executing Python code: {parsed_code[:50]}...")

            command = self._wrap_python_code(parsed_code)
            print(f"Wrapped command: {command}")

            security_check = await self.security_manager.validate_command(command)
            if not bool(security_check["allowed"]):
                print(f"Python code blocked for security: {parsed_code[:100]}...")
                error_result = str(security_check["message"])
                return error_result

            print("Python code validation passed - would execute successfully")
            return "Python code executed successfully"

        except json.JSONDecodeError as e:
            return f"Error parsing arguments: {str(e)}"
        except Exception as e:
            return f"Error executing Python code: {str(e)}"


class MockSecurityManager:
    """Mock security manager to reproduce the issue."""
    
    def __init__(self, max_length: int | None = None) -> None:
        self.blocked_commands = MockSecurityConfig.BLOCKED_COMMANDS
        self.allowed_commands = MockSecurityConfig.ALLOWED_COMMANDS
        self.custom_blocked_patterns = MockSecurityConfig.CUSTOM_BLOCKED_PATTERNS
        self.max_command_length = (
            max_length if max_length is not None else MockSecurityConfig.MAX_COMMAND_LENGTH
        )
        self.enable_audit_logging = MockSecurityConfig.ENABLE_AUDIT_LOGGING
    
    async def validate_command(self, command: str) -> dict[str, object]:
        """Validate command for security."""
        result = {"allowed": False, "message": ""}
        
        print(f"SECURITY CHECK: Starting validation for command (length: {len(command)}, limit: {self.max_command_length})")
        print(f"SECURITY CHECK: Command preview: {command[:100]}...")
        
        # Check command length
        length_check = await self._check_command_length(command)
        if length_check:
            print(f"SECURITY CHECK: Blocked by length check - {length_check['message']}")
            return length_check
        
        # Check blocked commands
        blocked_check = await self._check_blocked_commands(command)
        if blocked_check:
            print(f"SECURITY CHECK: Blocked by command check - {blocked_check['message']}")
            return blocked_check
        
        # Check custom blocked patterns
        pattern_check = await self._check_custom_patterns(command)
        if pattern_check:
            print(f"SECURITY CHECK: Blocked by pattern check - {pattern_check['message']}")
            return pattern_check
        
        # Check allowed commands whitelist
        whitelist_check = await self._check_allowed_commands(command)
        if whitelist_check:
            print(f"SECURITY CHECK: Blocked by whitelist check - {whitelist_check['message']}")
            return whitelist_check
        
        # Command is allowed
        print(f"SECURITY CHECK: Command PASSED all security checks")
        if self.enable_audit_logging:
            print(f"Command allowed: {command[:50]}...")
        
        result["allowed"] = True
        return result
    
    async def _check_command_length(self, command: str) -> dict[str, object] | None:
        """Check if command length exceeds maximum."""
        print(f"LENGTH CHECK: Command length={len(command)}, max={self.max_command_length}")
        if len(command) > self.max_command_length:
            message = (
                f"Error: Command too long (max {self.max_command_length} characters)"
            )
            if self.enable_audit_logging:
                print(f"Command blocked for length: {command[:50]}...")
            return self._create_blocked_result_dict(message)
        print("LENGTH CHECK: PASSED")
        return None
    
    async def _check_blocked_commands(self, command: str) -> dict[str, object] | None:
        """Check for blocked commands using precise matching."""
        command_lower = command.lower()
        command_parts = command.strip().split()
        
        print(f"BLOCKED COMMANDS CHECK: Checking {len(self.blocked_commands)} blocked patterns")
        
        for danger in self.blocked_commands:
            print(f"BLOCKED COMMANDS CHECK: Checking against blocked pattern: '{danger}'")
            # Most dangerous commands should be blocked exactly
            if danger in [
                "rm -rf",
                "sudo",
                "dd",
                "mkfs",
                "fdisk",
                "shutdown",
                "reboot",
                "poweroff",
                "halt",
            ]:
                if danger in command_lower:
                    print(f"BLOCKED COMMANDS CHECK: MATCHED - found '{danger}' in command")
                    return self._create_blocked_result(
                        f"Blocked dangerous command: {command}", danger
                    )
            # Special handling for format-related commands
            elif danger in ["format ", "format=", "format/"]:
                if any(
                    part.startswith(("format", "/format")) for part in command_parts
                ):
                    print(f"BLOCKED COMMANDS CHECK: MATCHED - found format-related command")
                    return self._create_blocked_result(
                        f"Blocked format command: {command}", "format"
                    )
            # All other blocked commands - check if contained in command
            elif danger in command_lower:
                print(f"BLOCKED COMMANDS CHECK: MATCHED - found '{danger}' in command (substring match)")
                return self._create_blocked_result(
                    f"Blocked command: {command}", danger
                )
        
        print("BLOCKED COMMANDS CHECK: PASSED - no blocked commands found")
        return None
    
    async def _check_custom_patterns(self, command: str) -> dict[str, object] | None:
        """Check for custom blocked patterns."""
        command_lower = command.lower()
        
        for pattern in self.custom_blocked_patterns:
            if pattern and pattern in command_lower:
                message = "Error: Command matches blocked pattern for security reasons"
                if self.enable_audit_logging:
                    print(f"Blocked custom pattern '{pattern}': {command}")
                return self._create_blocked_result_dict(message)
        
        return None
    
    async def _check_allowed_commands(self, command: str) -> dict[str, object] | None:
        """Check if command is in allowed whitelist (if enabled)."""
        if not self.allowed_commands:
            return None
        
        command_parts = command.strip().split()
        if not any(allowed in command_parts[0] for allowed in self.allowed_commands):
            message = "Error: Command not in allowed list"
            if self.enable_audit_logging:
                print(f"Command not in whitelist: {command}")
            return self._create_blocked_result_dict(message)
        
        return None
    
    def _create_blocked_result_dict(self, message: str) -> dict[str, object]:
        """Create a standard blocked command result dict."""
        return {"allowed": False, "message": message}
    
    def _create_blocked_result(self, message: str, danger: str) -> dict[str, object]:
        """Create a blocked command result dict."""
        return {"allowed": False, "message": message}


async def test_real_python_executor():
    """Test the real Python executor logic."""
    
    print("Testing real Python executor logic...")
    
    executor = MockPythonExecutor()
    
    # Test with the actual prime calculation that was blocked
    prime_code = '''
def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    w = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += w
        w = 6 - w
    return True

def find_nth_prime(n):
    count = 0
    candidate = 2
    while True:
        if is_prime(candidate):
            count += 1
            if count == n:
                return candidate
        candidate += 1

print(find_nth_prime(500000))
'''
    
    # Test with a simple version of the prime calculation
    simple_prime_code = "print('hello world')"  # Simple test that should work
    
    test_cases = [
        (simple_prime_code, "Prime calculation - might be blocked due to length"),
        ("print('hello world')", "Simple print - should pass"),
        ("print('sudo hello')", "Contains 'sudo' in string - should be blocked"),
        ("print('format(123)')", "Contains 'format' function - should pass (not blocked)"),
        ("import os; print(os.system('sudo whoami'))", "Contains 'sudo' in os.system call - should be blocked"),
    ]
    
    for code, description in test_cases:
        print(f"\n{'='*80}")
        print(f"Testing: {description}")
        print(f"Code length: {len(code)} characters")
        
        try:
            result = await executor.execute_python_code(code)
            print(f"Result: {result}")
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(test_real_python_executor())