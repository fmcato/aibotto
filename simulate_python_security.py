#!/usr/bin/env python3
"""
Check what happens when we simulate the actual Python executor behavior.
"""

import os

# Environment variables from Docker
MAX_COMMAND_LENGTH: int = int(os.getenv("MAX_COMMAND_LENGTH", "300000"))
MAX_PYTHON_CODE_LENGTH: int = int(os.getenv("MAX_PYTHON_CODE_LENGTH", "60000"))

print("=== CONFIGURATION ===")
print(f"Docker MAX_COMMAND_LENGTH: {MAX_COMMAND_LENGTH}")
print(f"SecurityConfig MAX_PYTHON_CODE_LENGTH: {MAX_PYTHON_CODE_LENGTH}")

def _wrap_python_code(code: str) -> str:
    """Wrap Python code for execution - matches real implementation."""
    if "\n" in code:
        return f"uv run python << 'EOF'\n{code}\nEOF"
    else:
        return f"uv run python -c '{code}'"

def simulate_python_executor_security():
    """Simulate the Python executor security validation."""
    
    print("\n=== SIMULATING PYTHON EXECUTOR ===")
    
    # Test cases
    test_cases = [
        "print('hello world')",
        "def is_prime(n): return n > 1 and all(n % i != 0 for i in range(2, int(n**0.5) + 1))\nprint(is_prime(500000))",
        """
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
""",
    ]
    
    for i, code in enumerate(test_cases):
        print(f"\n--- Test Case {i+1} ---")
        print(f"Original code length: {len(code)}")
        
        # Wrap the code (this is what Python executor does)
        wrapped_command = _wrap_python_code(code)
        print(f"Wrapped command: {wrapped_command[:100]}..." if len(wrapped_command) > 100 else f"Wrapped command: {wrapped_command}")
        print(f"Wrapped length: {len(wrapped_command)}")
        
        # Security checks
        length_check = len(wrapped_command) > MAX_COMMAND_LENGTH
        python_length_check = len(wrapped_command) > MAX_PYTHON_CODE_LENGTH
        
        print(f"Length check (MAX_COMMAND_LENGTH={MAX_COMMAND_LENGTH}): {'FAIL' if length_check else 'PASS'}")
        print(f"Python length check (MAX_PYTHON_CODE_LENGTH={MAX_PYTHON_CODE_LENGTH}): {'FAIL' if python_length_check else 'PASS'}")
        
        if length_check:
            print(f"❌ BLOCKED: Command too long for Docker environment")
        elif python_length_check:
            print(f"❌ BLOCKED: Command too long for Python executor")
        else:
            print(f"✅ ALLOWED: Command passes all security checks")

if __name__ == "__main__":
    simulate_python_executor_security()