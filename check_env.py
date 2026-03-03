#!/usr/bin/env python3
"""
Check environment variables and security config in Docker container.
"""

import os

# Check environment variables
print("Environment variables:")
print(f"MAX_COMMAND_LENGTH: {os.getenv('MAX_COMMAND_LENGTH')}")
print(f"MAX_PYTHON_CODE_LENGTH: {os.getenv('MAX_PYTHON_CODE_LENGTH', 'Not set')}")

# Simulate SecurityConfig behavior
MAX_COMMAND_LENGTH: int = int(os.getenv("MAX_COMMAND_LENGTH", "300000"))
MAX_PYTHON_CODE_LENGTH: int = int(os.getenv("MAX_PYTHON_CODE_LENGTH", "60000"))

print(f"\nSimulated SecurityConfig:")
print(f"MAX_COMMAND_LENGTH: {MAX_COMMAND_LENGTH}")
print(f"MAX_PYTHON_CODE_LENGTH: {MAX_PYTHON_CODE_LENGTH}")

# Test Python executor behavior
python_code = "print('hello world')"
wrapped_command = f"uv run python -c '{python_code}'"

print(f"\nPython code test:")
print(f"Original code: {python_code} (length: {len(python_code)})")
print(f"Wrapped command: {wrapped_command} (length: {len(wrapped_command)})")
print(f"Command length < MAX_COMMAND_LENGTH: {len(wrapped_command) < MAX_COMMAND_LENGTH}")
print(f"Command length < MAX_PYTHON_CODE_LENGTH: {len(wrapped_command) < MAX_PYTHON_CODE_LENGTH}")

# Test with longer code
long_python_code = """
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

print(find_nth_prime(1000))
"""

wrapped_long_command = f"uv run python << 'EOF'\n{long_python_code}\nEOF"
print(f"\nLong Python code test:")
print(f"Original code length: {len(long_python_code)}")
print(f"Wrapped command length: {len(wrapped_long_command)}")
print(f"Command length < MAX_COMMAND_LENGTH (1000): {len(wrapped_long_command) < 1000}")
print(f"Command length < MAX_PYTHON_CODE_LENGTH (60000): {len(wrapped_long_command) < 60000}")