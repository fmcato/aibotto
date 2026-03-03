#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '/app/src')

from aibotto.tools.executors.python_executor import PythonExecutor
from aibotto.tools.security import SecurityManager
from aibotto.config.security_config import SecurityConfig

print("=" * 80)
print("TESTING PYTHON EXECUTOR SECURITY")
print("=" * 80)

print(f"\nConfig:")
print(f"  MAX_PYTHON_CODE_LENGTH: {SecurityConfig.MAX_PYTHON_CODE_LENGTH}")
print(f"  MAX_COMMAND_LENGTH: {SecurityConfig.MAX_COMMAND_LENGTH}")
print(f"  BLOCKED_COMMANDS: {SecurityConfig.BLOCKED_COMMANDS}")

executor = PythonExecutor()
print(f"\nPythonExecutor initialized:")
print(f"  max_command_length: {executor.security_manager.max_command_length}")
print(f"  blocked_commands: {len(executor.security_manager.blocked_commands)} items")

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

wrapped = f"uv run python << 'EOF'\n{CODE}\nEOF"
print(f"\nTest code:")
print(f"  Code length: {len(CODE)}")
print(f"  Wrapped command length: {len(wrapped)}")
print(f"  Wrapped command preview: {wrapped[:100]}...")

async def test():
    print(f"\n{'=' * 80}")
    print("RUNNING SECURITY VALIDATION")
    print("=" * 80)

    result = await executor.security_manager.validate_command(wrapped)

    print(f"\nValidation result:")
    print(f"  ✓ Allowed: {result['allowed']}")
    print(f"  ✓ Message: {result.get('message', 'no message')}")

    if not result['allowed']:
        # Check what the issue is
        print(f"\nDebug - Testing individual checks:")

        manager = executor.security_manager

        # Test length
        if len(wrapped) > manager.max_command_length:
            print(f"  ✗ LENGTH: Exceeded (length={len(wrapped)}, max={manager.max_command_length})")
        else:
            print(f"  ✓ LENGTH: OK (length={len(wrapped)}, max={manager.max_command_length})")

        # Test blocked commands
        wrapped_lower = wrapped.lower()
        for danger in manager.blocked_commands:
            if danger in wrapped_lower:
                print(f"  ✗ BLOCKED COMMAND: Found '{danger}' in command")

asyncio.run(test())
