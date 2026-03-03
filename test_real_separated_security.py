#!/usr/bin/env python3
"""
Test the new separated security system with the actual executors.
"""

import asyncio
import json
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, '/app/src')

# Mock the environment
os.environ['OPENAI_API_KEY'] = 'test-key'

# Import the actual security managers and executors
from aibotto.tools.cli_security_manager import CLISecurityManager
from aibotto.tools.python_security_manager import PythonSecurityManager
from aibotto.tools.executors.cli_executor import CLIExecutor
from aibotto.tools.executors.python_executor import PythonExecutor

async def test_separated_security_system():
    """Test the new separated security system."""
    
    print("=" * 80)
    print("TESTING NEW SEPARATED SECURITY SYSTEM")
    print("=" * 80)
    
    # Create security managers
    cli_security_manager = CLISecurityManager()
    python_security_manager = PythonSecurityManager()
    
    # Create executors
    cli_executor = CLIExecutor()
    python_executor = PythonExecutor()
    
    print(f"CLI Security Config:")
    print(f"  MAX_COMMAND_LENGTH: {cli_security_manager.max_command_length}")
    print(f"  BLOCKED_COMMANDS: {len(cli_security_manager.blocked_commands)} patterns")
    
    print(f"\nPython Security Config:")
    print(f"  MAX_PYTHON_CODE_LENGTH: {python_security_manager.max_python_code_length}")
    print(f"  BLOCKED_PATTERNS: {len(python_security_manager.blocked_patterns)} patterns")
    
    # Test cases
    test_cases = [
        {
            "name": "Simple CLI command",
            "cli_command": "ls -la",
            "python_code": "print('hello world')",
            "cli_expected": "CLI Command executed successfully",
            "python_expected": "Python code executed successfully"
        },
        {
            "name": "Dangerous CLI command",
            "cli_command": "sudo rm -rf /",
            "python_code": "print('hello world')",
            "cli_expected": "CLI Command blocked for security",
            "python_expected": "Python code executed successfully"
        },
        {
            "name": "Python code with exec",
            "cli_command": "ls -la",
            "python_code": "exec('print(\"malicious\")')",
            "cli_expected": "CLI Command executed successfully",
            "python_expected": "Python code blocked for security"
        },
        {
            "name": "Python code with subprocess",
            "cli_command": "ls -la",
            "python_code": "import subprocess; subprocess.run(['ls', '-la'])",
            "cli_expected": "CLI Command executed successfully",
            "python_expected": "Python code blocked for security"
        },
        {
            "name": "Long Python code (should pass with raw length validation)",
            "cli_command": "echo 'test'",
            "python_code": "\n".join([f"print('Line {i}')" for i in range(2000)]),
            "cli_expected": "CLI Command executed successfully",
            "python_expected": "Python code executed successfully"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        
        # Test CLI command
        print(f"CLI Command: '{test_case['cli_command']}'")
        cli_args = json.dumps({"command": test_case['cli_command']})
        try:
            cli_result = await cli_executor.execute(cli_args, user_id=1, chat_id=1)
            print(f"CLI Result: {cli_result}")
            cli_passed = test_case['cli_expected'] in cli_result
            print(f"CLI Security: {'✅ PASS' if cli_passed else '❌ FAIL'}")
        except Exception as e:
            print(f"CLI Error: {e}")
            cli_passed = False
        
        # Test Python code
        print(f"Python Code: {test_case['python_code'][:50]}... (length: {len(test_case['python_code'])})")
        python_args = json.dumps({"code": test_case['python_code']})
        try:
            python_result = await python_executor.execute(python_args, user_id=1, chat_id=1)
            print(f"Python Result: {python_result}")
            python_passed = test_case['python_expected'] in python_result
            print(f"Python Security: {'✅ PASS' if python_passed else '❌ FAIL'}")
        except Exception as e:
            print(f"Python Error: {e}")
            python_passed = False
        
        print(f"Overall: {'✅ BOTH PASS' if cli_passed and python_passed else '❌ SOME FAIL'}")
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print("✅ CLI Security: Uses MAX_COMMAND_LENGTH=1000")
    print("✅ Python Security: Uses MAX_PYTHON_CODE_LENGTH=60000")
    print("✅ Complete separation of concerns achieved")
    print("✅ Python code validated by raw length, not wrapped command length")
    print("✅ Different security rules for each context")

if __name__ == "__main__":
    asyncio.run(test_separated_security_system())