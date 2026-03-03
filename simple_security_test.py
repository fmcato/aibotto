#!/usr/bin/env python3
"""
Simple test to reproduce the Python security issue.
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, '/app/src')

# Mock the environment
os.environ['OPENAI_API_KEY'] = 'test-key'

async def test_python_security():
    """Test Python code execution that should be blocked."""
    
    # Import the security manager directly
    from aibotto.tools.security import SecurityManager
    
    print("Testing Python security manager...")
    
    # Create security manager with Docker environment limits
    security_manager = SecurityManager(max_length=1000)  # Docker sets MAX_COMMAND_LENGTH=1000
    
    # Test commands that should be blocked due to substring matching
    test_cases = [
        ("sudo echo 'test'", "Should be blocked - contains 'sudo'"),
        ("python3 -c 'print(\"hello sudo world\")'", "Should be blocked - contains 'sudo' in string"),
        ("rm -rf /tmp/test", "Should be blocked - contains 'rm -rf'"),
        ("python3 -c 'import os; os.system(\"sudo something\")'", "Should be blocked - contains 'sudo'"),
        ("python3 -c 'print(format(123))'", "Should be blocked - contains 'format'"),
        ("python3 -c 'print(\"hello world\")'", "Should pass - no blocked substrings"),
    ]
    
    for command, description in test_cases:
        print(f"\nTesting: {description}")
        print(f"Command: {command}")
        
        try:
            result = await security_manager.validate_command(command)
            if result['allowed']:
                print("✅ ALLOWED")
            else:
                print(f"❌ BLOCKED: {result['message']}")
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_python_security())