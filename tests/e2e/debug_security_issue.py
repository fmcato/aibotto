"""
Debug the specific security issue with curl.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.aibotto.cli.security import SecurityManager


def debug_security_issue():
    """Debug the curl security issue."""
    print("=== Debugging Security Issue ===")
    
    security_manager = SecurityManager()
    
    # Check blocked commands
    print(f"Blocked commands: {security_manager.blocked_commands}")
    print(f"Allowed commands: {security_manager.allowed_commands}")
    
    # Test curl command step by step
    curl_command = "curl 'https://wttr.in/London?format=3'"
    print(f"\nTesting command: {curl_command}")
    print(f"Command lower: {curl_command.lower()}")
    
    # Check each blocked command
    for danger in security_manager.blocked_commands:
        if danger in curl_command.lower():
            print(f"❌ BLOCKED: '{danger}' found in command")
        else:
            print(f"✅ OK: '{danger}' not found in command")
    
    # Test the actual validation
    result = security_manager.validate_command(curl_command)
    print(f"\nValidation result: {result}")
    
    # Test with a simple curl
    simple_curl = "curl wttr.in"
    print(f"\nTesting simple command: {simple_curl}")
    result = security_manager.validate_command(simple_curl)
    print(f"Simple curl result: {result}")


if __name__ == "__main__":
    debug_security_issue()