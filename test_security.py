import asyncio
import sys
sys.path.insert(0, "/app/src")

from aibotto.tools.security import SecurityManager

# The actual problematic code from Docker logs
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

    # Test with Python executor's max length (60000)
    manager_python = SecurityManager(max_length=60000)
    print(f"\nPython executor max length: {manager_python.max_command_length}")

    result = await manager_python.validate_command(FULL_COMMAND)
    print(f"\nSecurity result (Python executor):")
    print(f"  Allowed: {result['allowed']}")
    print(f"  Message: {result['message'] if result['message'] else 'No message'}")

    # Test with CLI max length (from Docker = 1000)
    manager_cli = SecurityManager(max_length=1000)
    print(f"\nCLI executor max length: {manager_cli.max_command_length}")

    result = await manager_cli.validate_command(FULL_COMMAND)
    print(f"\nSecurity result (CLI executor limit):")
    print(f"  Allowed: {result['allowed']}")
    print(f"  Message: {result['message'] if result['message'] else 'No message'}")

if __name__ == "__main__":
    asyncio.run(main())
