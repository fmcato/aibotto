"""
Unit tests for PythonExecutor.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from src.aibotto.tools.executors.python_executor import PythonExecutor
from src.aibotto.config.security_config import SecurityConfig


@pytest.fixture
def python_executor():
    """Create a PythonExecutor instance for testing."""
    with patch("src.aibotto.tools.executors.python_executor.PythonSecurityManager"):
        executor = PythonExecutor()
        executor.security_manager = MagicMock()
        executor.security_manager.validate_python_code = AsyncMock(return_value={"allowed": True})
        return executor


@pytest.mark.asyncio
class TestPythonExecutor:
    """Test cases for PythonExecutor class."""

    async def test_wrap_python_code_single_line(self, python_executor):
        """Test wrapping single-line Python code."""
        code = "import math; print(math.pi)"
        result = python_executor._wrap_python_code(code)
        assert result == "uv run python -c 'import math; print(math.pi)'"

    async def test_wrap_python_code_multiline(self, python_executor):
        """Test wrapping multi-line Python code with heredoc."""
        code = "def func():\n    return 42\nprint(func())"
        result = python_executor._wrap_python_code(code)
        assert result == "uv run python << 'EOF'\ndef func():\n    return 42\nprint(func())\nEOF"

    async def test_wrap_python_code_with_newline_in_middle(self, python_executor):
        """Test wrapping code with newline in middle uses heredoc."""
        code = "x = 1\ny = 2"
        result = python_executor._wrap_python_code(code)
        assert "uv run python << 'EOF'" in result
        assert "x = 1" in result
        assert "y = 2" in result
        assert "EOF" in result

    async def test_execute_success_single_line(self, python_executor):
        """Test successful execution of single-line Python code."""
        python_executor.security_manager.validate_python_code = AsyncMock(return_value={"allowed": True})

        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"3.14159\n", b""))
            mock_subprocess.return_value = mock_process

            result = await python_executor.execute('{"code": "import math; print(math.pi)"}')

            assert "3.14159" in result
            mock_subprocess.assert_called_once()

            # Verify command was wrapped correctly
            call_args = mock_subprocess.call_args[0][0]
            assert "uv run python -c" in call_args

    async def test_execute_success_multiline(self, python_executor):
        """Test successful execution of multi-line Python code."""
        python_executor.security_manager.validate_python_code = AsyncMock(return_value={"allowed": True})

        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"42\n", b""))
            mock_subprocess.return_value = mock_process

            code = "def func():\\n    return 42\\nprint(func())"
            json_args = f'{{"code": "{code}"}}'
            result = await python_executor.execute(json_args)

            assert "42" in result

            # Verify heredoc syntax was used
            call_args = mock_subprocess.call_args[0][0]
            assert "uv run python << 'EOF'" in call_args
            assert "EOF" in call_args

    async def test_execute_with_db_ops(self, python_executor):
        """Test execution with database operations."""
        python_executor.security_manager.validate_python_code = AsyncMock(return_value={"allowed": True})
        mock_db_ops = MagicMock()
        mock_db_ops.save_message_compat = AsyncMock()

        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"42\n", b""))
            mock_subprocess.return_value = mock_process

            result = await python_executor.execute(
                '{"code": "print(42)"}', user_id=123, db_ops=mock_db_ops, chat_id=456
            )

            assert "42" in result
            mock_db_ops.save_message_compat.assert_called_once_with(
                user_id=123, chat_id=456, role="system", content=result
            )

    async def test_execute_no_code_provided(self, python_executor):
        """Test execution with no code provided."""
        result = await python_executor.execute('{"other": "field"}')
        assert "No code provided" in result

    async def test_execute_invalid_json(self, python_executor):
        """Test execution with invalid JSON arguments."""
        result = await python_executor.execute("invalid json")
        assert "Error parsing arguments" in result

    async def test_execute_security_blocked(self, python_executor):
        """Test execution blocked by security manager."""
        python_executor.security_manager.validate_python_code = AsyncMock(
            return_value={"allowed": False, "message": "Blocked for security"}
        )

        result = await python_executor.execute('{"code": "print(1)"}')

        assert "Blocked for security" in result
        python_executor.security_manager.validate_python_code.assert_called_once()

    async def test_execute_security_blocked_with_db_ops(self, python_executor):
        """Test security blocked execution logs to database."""
        python_executor.security_manager.validate_python_code = AsyncMock(
            return_value={"allowed": False, "message": "Blocked for security"}
        )
        mock_db_ops = MagicMock()
        mock_db_ops.save_message_compat = AsyncMock()

        result = await python_executor.execute(
            '{"code": "print(1)"}', user_id=123, db_ops=mock_db_ops, chat_id=456
        )

        assert "Blocked for security" in result
        mock_db_ops.save_message_compat.assert_called_once_with(
            user_id=123, chat_id=456, role="system", content=result
        )

    async def test_execute_python_error(self, python_executor):
        """Test execution with Python runtime error."""
        python_executor.security_manager.validate_python_code = AsyncMock(return_value={"allowed": True})

        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b"", b"NameError: name 'x' is not defined\n"))
            mock_subprocess.return_value = mock_process

            result = await python_executor.execute('{"code": "print(x)"}')

            assert "Error" in result
            assert "NameError" in result

    async def test_execute_python_error_with_db_ops(self, python_executor):
        """Test Python error logs to database."""
        python_executor.security_manager.validate_python_code = AsyncMock(return_value={"allowed": True})
        mock_db_ops = MagicMock()
        mock_db_ops.save_message_compat = AsyncMock()

        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b"", b"Error message\n"))
            mock_subprocess.return_value = mock_process

            result = await python_executor.execute(
                '{"code": "print(x)"}', user_id=123, db_ops=mock_db_ops, chat_id=456
            )

            assert "Error" in result
            mock_db_ops.save_message_compat.assert_called_once_with(
                user_id=123, chat_id=456, role="system", content=result
            )

    async def test_execute_exception(self, python_executor):
        """Test execution with unexpected exception."""
        python_executor.security_manager.validate_python_code = AsyncMock(return_value={"allowed": True})

        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_subprocess.side_effect = OSError("Subprocess failed")

            result = await python_executor.execute('{"code": "print(1)"}')

            assert "Error executing Python code" in result

    async def test_complex_multiline_script(self, python_executor):
        """Test execution of complex multi-line algorithm."""
        python_executor.security_manager.validate_python_code = AsyncMock(return_value={"allowed": True})

        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"2\n3\n5\n7\n", b""))
            mock_subprocess.return_value = mock_process

            code = "def sieve(n):\\n    is_prime = [True] * (n+1)\\n    is_prime[0] = is_prime[1] = False\\n    for i in range(2, int(n**0.5)+1):\\n        if is_prime[i]:\\n            for j in range(i*i, n+1, i):\\n                is_prime[j] = False\\n    return [i for i, prime in enumerate(is_prime) if prime]\\n\\nprimes = sieve(10)\\nfor p in primes:\\n    print(p)"
            json_args = f'{{"code": "{code}"}}'
            result = await python_executor.execute(json_args)

            assert "2" in result
            assert "3" in result
            assert "5" in result
            assert "7" in result

            # Verify heredoc was used
            call_args = mock_subprocess.call_args[0][0]
            assert "uv run python << 'EOF'" in call_args

    async def test_code_with_quotes(self, python_executor):
        """Test execution of code containing quotes."""
        python_executor.security_manager.validate_python_code = AsyncMock(return_value={"allowed": True})

        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"hello world test\n", b""))
            mock_subprocess.return_value = mock_process

            code = "print('hello world test')"
            result = await python_executor.execute(f'{{"code": "{code}"}}')

            assert "hello" in result

    async def test_code_with_backslashes(self, python_executor):
        """Test execution of code containing backslashes."""
        python_executor.security_manager.validate_python_code = AsyncMock(return_value={"allowed": True})

        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"C:\\\\path\\\\to\\\\file\n", b""))
            mock_subprocess.return_value = mock_process

            code = "import os; print(os.path.join('C:\\\\\\\\path', 'to', 'file'))"
            result = await python_executor.execute(f'{{"code": "{code}"}}')

            assert "path" in result

    async def test_output_decoding_with_errors(self, python_executor):
        """Test output decoding with non-UTF-8 characters."""
        python_executor.security_manager.validate_python_code = AsyncMock(return_value={"allowed": True})

        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"output\xff\xfe", b""))
            mock_subprocess.return_value = mock_process

            result = await python_executor.execute('{"code": "print(1)"}')

            assert "output" in result
