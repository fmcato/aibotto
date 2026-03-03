#!/usr/bin/env python3

import asyncio
import sys
import json


# The exact Python code that was blocked in the Docker logs
FOUND_PRIME_CODE = """import math
import time

def estimate_nth_prime_upper_bound(n):
    \"\"\"Estimate upper bound for nth prime using known approximations\"\"\"
    # For n >= 6, n*(log(n) + log(log(n))) works well
    if n < 6:
        return 13  # small primes
    log_n = math.log(n)
    log_log_n = math.log(log_n)
    upper_bound = int(n * (log_n + log_log_n))
    # Add a safety margin (30%)
    return int(upper_bound * 1.3)

def sieve_of_eratosthenes(limit):
    \"\"\"Generate primes up to limit using Sieve of Eratosthenes\"\"\"
    is_prime = bytearray(b'\\x01') * (limit + 1)
    is_prime[0] = is_prime[1] = 0
    
    sqrt_limit = int(math.isqrt(limit))
    for i in range(2, sqrt_limit + 1):
        if is_prime[i]:
            start = i * i
            step = i
            for j in range(start, limit + 1, step):
                is_prime[j] = 0
    
    # Count primes to ensure we have enough
    primes = []
    for i in range(2, limit + 1):
        if is_prime[i]:
            primes.append(i)
            if len(primes) >= 500000:  # We only need up to 500,000th
                break
    return primes

def main():
    n = 500000
    print(f"Calculating the {n:,}th prime number...")
    
    # Step 1: Estimate upper bound
    start_time = time.time()
    estimated_limit = estimate_nth_prime_upper_bound(n)
    print(f"Estimated upper bound: {estimated_limit:,}")
    
    # Step 2: Generate primes using sieve
    print("Generating primes with Sieve of Eratosthenes...")
    primes = sieve_of_eratosthenes(estimated_limit)
    
    if len(primes) >= n:
        result = primes[n-1]  # Zero-indexed
        elapsed = time.time() - start_time
        print(f"\\nThe {n:,}th prime number is: {result:,}")
        print(f"Total primes found: {len(primes):,}")
        print(f"Time taken: {elapsed:.2f} seconds")
        return result
    else:
        print(f"Need more primes. Found {len(primes)} primes, need {n}")
        print("Increasing upper bound and retrying...")
        # Increase bound and try again
        new_limit = int(estimated_limit * 1.5)
        primes = sieve_of_eratosthenes(new_limit)
        if len(primes) >= n:
            result = primes[n-1]
            elapsed = time.time() - start_time
            print(f"\\nThe {n:,}th prime number is: {result:,}")
            print(f"Total primes found: {len(primes):,}")
            print(f"Time taken: {elapsed:.2f} seconds")
            return result
        else:
            print(f"Still insufficient. Found {len(primes)} primes, need {n}")
            return None

if __name__ == "__main__":
    main()
"""


async def test_python_security():
    """Test Python code security checking"""
    from aibotto.tools.executors.python_executor import PythonExecutor

    print("=" * 80)
    print("TESTING PYTHON CODE SECURITY")
    print("=" * 80)

    executor = PythonExecutor()
    print(f"PythonExecutor initialized")
    print(f"  Max code length: {executor.security_manager.max_command_length}")

    print("\n" + "=" * 80)
    print(f"CODE LENGTH: {len(FOUND_PRIME_CODE)} characters")
    print("=" * 80)

    print("\n" + "=" * 80)
    print("ATTEMPTING TO EXECUTE PRIME CALCULATION CODE...")
    print("=" * 80)

    arguments = json.dumps({"code": FOUND_PRIME_CODE})
    result = await executor.execute(arguments, user_id=999999, db_ops=None, chat_id=999999)

    print("\n" + "=" * 80)
    print(f"RESULT: {result[:200]}")
    print("=" * 80)

    # Also test with a simpler code that should work
    print("\n" + "=" * 80)
    print("TESTING WITH SIMPLE CODE (should work)...")
    print("=" * 80)

    simple_code = "print('Hello, World!')"
    print(f"Simple code length: {len(simple_code)} characters")

    arguments = json.dumps({"code": simple_code})
    result = await executor.execute(arguments, user_id=999999, db_ops=None, chat_id=999999)
    print(f"Simple code result: {result}")

if __name__ == "__main__":
    asyncio.run(test_python_security())
