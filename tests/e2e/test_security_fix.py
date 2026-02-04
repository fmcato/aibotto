"""
Test the security fix for curl commands.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio

from src.aibotto.cli.security import SecurityManager


async def test_security_fix():
    """Test if curl commands are now allowed."""
    print("=== Testing Security Fix ===")
    
    security_manager = SecurityManager()
    
    # Test curl commands that should be allowed
    curl_commands = [
        "curl 'https://wttr.in/London?format=3'",
        "curl wttr.in",
        "curl -s 'https://api.weather.com/weather'",
        "curl https://jsonplaceholder.typicode.com/posts/1"
    ]
    
    for cmd in curl_commands:
        result = await security_manager.validate_command(cmd)
        if result["allowed"]:
            print(f"✅ '{cmd}' - ALLOWED")
        else:
            print(f"❌ '{cmd}' - BLOCKED: {result['message']}")
    
    # Test commands that should still be blocked
    blocked_commands = [
        "sudo rm -rf /",
        "mkfs /dev/sda1",
        "format /dev/sda1",
        "shutdown -h now"
    ]
    
    print("\n=== Testing Blocked Commands ===")
    for cmd in blocked_commands:
        result = await security_manager.validate_command(cmd)
        if not result["allowed"]:
            print(f"✅ '{cmd}' - BLOCKED: {result['message']}")
        else:
            print(f"❌ '{cmd}' - ALLOWED (should be blocked!)")


if __name__ == "__main__":
    asyncio.run(test_security_fix())