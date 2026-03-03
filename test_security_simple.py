import asyncio
import sys
import os

# Direct import without using the full package structure
sys.path.insert(0, "/app/src")

# Import just the security config directly
exec(open("/app/src/aibotto/config/security_config.py").read())

# Import and create logger
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define SecurityManager inline
class SecurityManager:
    def __init__(self, max_length=None):
        self.blocked_commands = BLOCKED_COMMANDS
        self.allowed_commands = ALLOWED_COMMANDS
        self.custom_blocked_patterns = CUSTOM_BLOCKED_PATTERNS
        self.max_command_length = max_length if max_length is not None else MAX_COMMAND_LENGTH
        self.enable_audit_logging = ENABLE_AUDIT_LOGGING

    async def validate_command(self, command):
        result = {"allowed": False, "message": ""}

        logger.debug(f"SECURITY CHECK: Starting validation for command (length: {len(command)}, limit: {self.max_command_length})")
        logger.debug(f"SECURITY CHECK: Command preview: {command[:100]}...")

        # Check command length
        length_check = await self._check_command_length(command)
        if length_check:
            logger.warning(f"SECURITY CHECK: Blocked by length check - {length_check['message']}")
            return length_check

        # Check blocked commands
        blocked_check = await self._check_blocked_commands(command)
        if blocked_check:
            logger.warning(f"SECURITY CHECK: Blocked by command check - {blocked_check['message']}")
            return blocked_check

        # Check custom blocked patterns
        pattern_check = await self._check_custom_patterns(command)
        if pattern_check:
            logger.warning(f"SECURITY CHECK: Blocked by pattern check - {pattern_check['message']}")
            return pattern_check

        # Check allowed commands whitelist
        whitelist_check = await self._check_allowed_commands(command)
        if whitelist_check:
            logger.warning(f"SECURITY CHECK: Blocked by whitelist check - {whitelist_check['message']}")
            return whitelist_check

        logger.info(f"SECURITY CHECK: Command PASSED all security checks")

        result["allowed"] = True
        return result

    async def _check_command_length(self, command):
        logger.debug(f"LENGTH CHECK: Command length={len(command)}, max={self.max_command_length}")
        if len(command) > self.max_command_length:
            message = f"Error: Command too long (max {self.max_command_length} characters)"
            if self.enable_audit_logging:
                logger.warning(f"Command blocked for length: {command[:50]}...")
            return {"allowed": False, "message": message}
        logger.debug("LENGTH CHECK: PASSED")
        return None

    async def _check_blocked_commands(self, command):
        command_lower = command.lower()
        command_parts = command.strip().split()

        logger.debug(f"BLOCKED COMMANDS CHECK: Checking {len(self.blocked_commands)} blocked patterns")

        for danger in self.blocked_commands:
            logger.debug(f"BLOCKED COMMANDS CHECK: Checking against blocked pattern: '{danger}'")

            if danger in [
                "rm -rf", "sudo", "dd", "mkfs", "fdisk", "shutdown", "reboot", "poweroff", "halt"
            ]:
                if danger in command_lower:
                    logger.warning(f"BLOCKED COMMANDS CHECK: MATCHED - found '{danger}' in command")
                    return {"allowed": False, "message": f"Blocked dangerous command: {command}"}

            elif danger in ["format ", "format=", "format/"]:
                if any(part.startswith(("format", "/format")) for part in command_parts):
                    logger.warning(f"BLOCKED COMMANDS CHECK: MATCHED - found format-related command")
                    return {"allowed": False, "message": f"Blocked format command: {command}"}

            elif danger in command_lower:
                logger.warning(f"BLOCKED COMMANDS CHECK: MATCHED - found '{danger}' in command (substring match)")
                return {"allowed": False, "message": f"Blocked command: {command}"}

        logger.debug("BLOCKED COMMANDS CHECK: PASSED - no blocked commands found")
        return None

    async def _check_custom_patterns(self, command):
        command_lower = command.lower()
        for pattern in self.custom_blocked_patterns:
            if pattern and pattern in command_lower:
                message = "Error: Command matches blocked pattern for security reasons"
                if self.enable_audit_logging:
                    logger.warning(f"Blocked custom pattern '{pattern}': {command}")
                return {"allowed": False, "message": message}
        return None

    async def _check_allowed_commands(self, command):
        if not self.allowed_commands:
            return None

        command_parts = command.strip().split()
        if not any(allowed in command_parts[0] for allowed in self.allowed_commands):
            message = "Error: Command not in allowed list"
            if self.enable_audit_logging:
                logger.warning(f"Command not in whitelist: {command}")
            return {"allowed": False, "message": message}
        return None

CODE = """import math
import time

def estimate_nth_prime_upper_bound(n):
    if n < 6:
        return 13
    log_n = math.log(n)
    log_log_n = math.log(log_n)
    upper_bound = int(n * (log_n + log_log_n))
    return int(upper_bound * 1.3)

def sieve_of_eratosthenes(limit):
    is_prime = bytearray(b'\\x01') * (limit + 1)
    is_prime[0] = is_prime[1] = 0
    sqrt_limit = int(math.isqrt(limit))
    for i in range(2, sqrt_limit + 1):
        if is_prime[i]:
            start = i * i
            step = i
            for j in range(start, limit + 1, step):
                is_prime[j] = 0
    primes = []
    for i in range(2, limit + 1):
        if is_prime[i]:
            primes.append(i)
            if len(primes) >= 500000:
                break
    return primes
"""

FULL_COMMAND = f"uv run python << 'EOF'\n{CODE}\nEOF"

async def main():
    print("=" * 80)
    print("TESTING SECURITY VALIDATION")
    print("=" * 80)
    print(f"\nCode length: {len(CODE)} characters")
    print(f"Full command length: {len(FULL_COMMAND)} characters")
    print(f"\nCurrently set env MAX_COMMAND_LENGTH: {os.getenv('MAX_COMMAND_LENGTH', 'not set')}")

    # Test with Python executor's max length (60000)
    print("\n" + "=" * 80)
    print("TEST 1: Python executor (max_length=60000)")
    print("=" * 80)
    manager_python = SecurityManager(max_length=60000)
    print(f"Manager max length: {manager_python.max_command_length}")

    result = await manager_python.validate_command(FULL_COMMAND)
    print(f"\n✓ Security result (Python executor):")
    print(f"  Allowed: {result['allowed']}")
    print(f"  Message: {result['message'] if result.get('message') else 'No message'}")

    # Test with CLI max length (from Docker = 1000)
    print("\n" + "=" * 80)
    print("TEST 2: CLI executor (max_length=1000)")
    print("=" * 80)
    manager_cli = SecurityManager(max_length=1000)
    print(f"Manager max length: {manager_cli.max_command_length}")

    result = await manager_cli.validate_command(FULL_COMMAND)
    print(f"\n✓ Security result (CLI executor limit):")
    print(f"  Allowed: {result['allowed']}")
    print(f"  Message: {result['message'] if result.get('message') else 'No message'}")

if __name__ == "__main__":
    asyncio.run(main())
