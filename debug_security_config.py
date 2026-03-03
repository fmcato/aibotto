#!/usr/bin/env python3
"""
Debug the SecurityConfig values in Docker environment.
"""

import os

# Check environment variables
print("=== ENVIRONMENT VARIABLES ===")
print(f"os.getenv('MAX_COMMAND_LENGTH'): {os.getenv('MAX_COMMAND_LENGTH')}")
print(f"os.getenv('MAX_PYTHON_CODE_LENGTH'): {os.getenv('MAX_PYTHON_CODE_LENGTH')}")

# Check what the actual SecurityConfig would be
print("\n=== SECURITYCONFIG SIMULATION ===")
MAX_COMMAND_LENGTH: int = int(os.getenv("MAX_COMMAND_LENGTH", "300000"))
print(f"MAX_COMMAND_LENGTH = int(os.getenv('MAX_COMMAND_LENGTH', '300000')) = {MAX_COMMAND_LENGTH}")

MAX_PYTHON_CODE_LENGTH: int = int(os.getenv("MAX_PYTHON_CODE_LENGTH", "60000"))
print(f"MAX_PYTHON_CODE_LENGTH = int(os.getenv('MAX_PYTHON_CODE_LENGTH', '60000')) = {MAX_PYTHON_CODE_LENGTH}")

# Test what happens when os.getenv returns None
print("\n=== TESTING WITH NONE VALUES ===")
test_cmd_length = int(os.getenv("MAX_COMMAND_LENGTH", "300000"))
test_python_length = int(os.getenv("MAX_PYTHON_CODE_LENGTH", "60000"))

print(f"If os.getenv('MAX_COMMAND_LENGTH') is None: {os.getenv('MAX_COMMAND_LENGTH')}")
print(f"int(os.getenv('MAX_COMMAND_LENGTH', '300000')) = {test_cmd_length}")

print(f"If os.getenv('MAX_PYTHON_CODE_LENGTH') is None: {os.getenv('MAX_PYTHON_CODE_LENGTH')}")
print(f"int(os.getenv('MAX_PYTHON_CODE_LENGTH', '60000')) = {test_python_length}")

# Test SecurityManager behavior
print("\n=== SECURITYMANAGER SIMULATION ===")
def simulate_security_manager_init(max_length=None):
    """Simulate SecurityManager.__init__ behavior"""
    if max_length is not None:
        actual_max_length = max_length
    else:
        actual_max_length = int(os.getenv("MAX_COMMAND_LENGTH", "300000"))
    
    print(f"SecurityManager(max_length={max_length})")
    print(f"  max_length provided: {max_length}")
    print(f"  actual max_command_length: {actual_max_length}")
    return actual_max_length

# Test different scenarios
print("\n--- Scenario 1: PythonExecutor calls SecurityManager(max_length=SecurityConfig.MAX_PYTHON_CODE_LENGTH)")
python_config_length = int(os.getenv("MAX_PYTHON_CODE_LENGTH", "60000"))
result1 = simulate_security_manager_init(max_length=python_config_length)

print("\n--- Scenario 2: SecurityManager called with max_length=None")
result2 = simulate_security_manager_init(max_length=None)

print(f"\nResult 1 (PythonExecutor): {result1}")
print(f"Result 2 (None fallback): {result2}")

# The expected behavior
print(f"\n=== EXPECTED BEHAVIOR ===")
print(f"PythonExecutor should pass max_length=60000")
print(f"SecurityManager should use that 60000 value")
print(f"Actual result from PythonExecutor: {result1}")
print(f"✅ Correct: {result1 == 60000}")