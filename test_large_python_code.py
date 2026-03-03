#!/usr/bin/env python3
"""
Test with even larger Python code to see if we can trigger the length issue.
"""

import os

# Environment variables from Docker
MAX_COMMAND_LENGTH: int = int(os.getenv("MAX_COMMAND_LENGTH", "300000"))
MAX_PYTHON_CODE_LENGTH: int = int(os.getenv("MAX_PYTHON_CODE_LENGTH", "60000"))

print("=== TESTING WITH LARGER PYTHON CODE ===")
print(f"Docker MAX_COMMAND_LENGTH: {MAX_COMMAND_LENGTH}")
print(f"SecurityConfig MAX_PYTHON_CODE_LENGTH: {MAX_PYTHON_CODE_LENGTH}")

def _wrap_python_code(code: str) -> str:
    """Wrap Python code for execution - matches real implementation."""
    if "\n" in code:
        return f"uv run python << 'EOF'\n{code}\nEOF"
    else:
        return f"uv run python -c '{code}'"

# Create a very large Python code that would exceed Docker's limit
large_prime_code = """
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

# Find the 500000th prime number
result = find_nth_prime(500000)
print(f"The 500000th prime number is: {result}")
"""

# Create an extremely large code to test boundaries
extremely_large_code = """
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

# Find the 500000th prime number
result = find_nth_prime(500000)
print(f"The 500000th prime number is: {result}")

# Add some extra processing to make it longer
primes_found = []
for i in range(1, 1000):
    if is_prime(i):
        primes_found.append(i)

print(f"Found {len(primes_found)} primes under 1000")

# More processing
square_primes = [p*p for p in primes_found if p < 100]
print(f"Square of primes under 100: {square_primes}")

# Even more processing
prime_sums = []
for i in range(len(primes_found)-1):
    prime_sums.append(primes_found[i] + primes_found[i+1])

print(f"Sum of consecutive primes: {prime_sums[:10]}...")

# Final processing
final_result = {
    '500000th_prime': result,
    'total_primes_found': len(primes_found),
    'square_primes': square_primes,
    'consecutive_sums': prime_sums[:10]
}

print("Final result:", final_result)
"""

test_cases = [
    ("Large prime code", large_prime_code),
    ("Extremely large code", extremely_large_code),
    ("Test boundary", "x" * 800),  # Test with exactly 800 chars
]

for name, code in test_cases:
    print(f"\n--- {name} ---")
    print(f"Original code length: {len(code)}")
    
    # Wrap the code (this is what Python executor does)
    wrapped_command = _wrap_python_code(code)
    print(f"Wrapped length: {len(wrapped_command)}")
    
    # Security checks
    length_check = len(wrapped_command) > MAX_COMMAND_LENGTH
    python_length_check = len(wrapped_command) > MAX_PYTHON_CODE_LENGTH
    
    print(f"Length check (MAX_COMMAND_LENGTH={MAX_COMMAND_LENGTH}): {'FAIL' if length_check else 'PASS'}")
    print(f"Python length check (MAX_PYTHON_CODE_LENGTH={MAX_PYTHON_CODE_LENGTH}): {'FAIL' if python_length_check else 'PASS'}")
    
    if length_check:
        print(f"❌ BLOCKED: Command too long for Docker environment")
        print(f"   Exceeded by: {len(wrapped_command) - MAX_COMMAND_LENGTH} characters")
    elif python_length_check:
        print(f"❌ BLOCKED: Command too long for Python executor")
        print(f"   Exceeded by: {len(wrapped_command) - MAX_PYTHON_CODE_LENGTH} characters")
    else:
        print(f"✅ ALLOWED: Command passes all security checks")