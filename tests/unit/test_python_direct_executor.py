"""Unit tests for PythonDirectExecutor."""

import asyncio

import pytest

from src.aibotto.tools.executors.python_direct_executor import PythonDirectExecutor


class TestPythonDirectExecutor:
    """Test cases for PythonDirectExecutor class."""

    @pytest.fixture
    def executor(self):
        """Create a PythonDirectExecutor instance for testing."""
        return PythonDirectExecutor()

    @pytest.mark.asyncio
    async def test_execute_simple_print(self, executor):
        """Test simple print execution."""
        result = await executor.execute('print("hello")')
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_execute_math_calculation(self, executor):
        """Test math calculation execution."""
        result = await executor.execute('print(2 + 2 * 2)')
        assert result == "6"

    @pytest.mark.asyncio
    async def test_execute_multiline_code(self, executor):
        """Test multiline Python code execution."""
        code = """
x = 10
y = 20
print(x + y)
"""
        result = await executor.execute(code)
        assert result == "30"

    @pytest.mark.asyncio
    async def test_execute_with_imports(self, executor):
        """Test code with standard library imports."""
        code = """
import math
print(math.pi)
"""
        result = await executor.execute(code)
        assert result.startswith("3.14159")

    @pytest.mark.asyncio
    async def test_execute_syntax_error(self, executor):
        """Test handling of syntax errors."""
        result = await executor.execute('print(2+')
        assert "SyntaxError" in result
        assert result.startswith("Error:")

    @pytest.mark.asyncio
    async def test_execute_runtime_error(self, executor):
        """Test handling of runtime errors."""
        result = await executor.execute('print(undefined_variable)')
        assert "NameError" in result
        assert result.startswith("Error:")

    @pytest.mark.asyncio
    async def test_execute_zero_division_error(self, executor):
        """Test handling of zero division error."""
        result = await executor.execute('print(1/0)')
        assert "ZeroDivisionError" in result
        assert result.startswith("Error:")

    @pytest.mark.asyncio
    async def test_execute_no_output(self, executor):
        """Test code that produces no output."""
        result = await executor.execute('x = 1 + 1')
        assert result == "Script executed but produced no output"

    @pytest.mark.asyncio
    async def test_execute_empty_code(self, executor):
        """Test handling of empty code."""
        result = await executor.execute('')
        assert "Error" in result
        assert "empty" in result.lower()

    @pytest.mark.asyncio
    async def test_execute_whitespace_only(self, executor):
        """Test handling of whitespace-only code."""
        result = await executor.execute('   \n\t  ')
        assert "Error" in result
        assert "empty" in result.lower() or "whitespace" in result.lower()

    @pytest.mark.asyncio
    async def test_execute_timeout(self, executor):
        """Test execution timeout."""
        code = 'import time; time.sleep(60)'
        result = await executor.execute(code)
        assert "Timeout" in result
        assert "45" in result

    @pytest.mark.asyncio
    async def test_execute_function_definition(self, executor):
        """Test defining and calling a function."""
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))
"""
        result = await executor.execute(code)
        assert result == "120"

    @pytest.mark.asyncio
    async def test_execute_list_comprehension(self, executor):
        """Test list comprehension execution."""
        code = 'print([x**2 for x in range(5)])'
        result = await executor.execute(code)
        assert result == "[0, 1, 4, 9, 16]"

    @pytest.mark.asyncio
    async def test_execute_dictionary_operations(self, executor):
        """Test dictionary operations."""
        code = """
data = {"a": 1, "b": 2}
data["c"] = 3
print(sorted(data.keys()))
"""
        result = await executor.execute(code)
        assert result == "['a', 'b', 'c']"

    @pytest.mark.asyncio
    async def test_execute_with_user_id(self, executor):
        """Test execution with user_id parameter."""
        result = await executor.execute('print("test")', user_id=123)
        assert result == "test"

    @pytest.mark.asyncio
    async def test_execute_with_chat_id(self, executor):
        """Test execution with chat_id parameter."""
        result = await executor.execute('print("test")', chat_id=456)
        assert result == "test"

    @pytest.mark.asyncio
    async def test_execute_multiple_prints(self, executor):
        """Test multiple print statements."""
        code = """
print("line 1")
print("line 2")
print("line 3")
"""
        result = await executor.execute(code)
        assert result == "line 1\nline 2\nline 3"

    @pytest.mark.asyncio
    async def test_execute_print_with_separator(self, executor):
        """Test print with custom separator."""
        result = await executor.execute('print("a", "b", "c", sep="-")')
        assert result == "a-b-c"

    @pytest.mark.asyncio
    async def test_execute_print_no_newline(self, executor):
        """Test print without newline."""
        result = await executor.execute('print("hello", end=""); print("world")')
        assert result == "helloworld"

    @pytest.mark.asyncio
    async def test_execute_json_import(self, executor):
        """Test importing and using json module."""
        code = """
import json
data = {"key": "value"}
print(json.dumps(data))
"""
        result = await executor.execute(code)
        assert result == '{"key": "value"}'

    @pytest.mark.asyncio
    async def test_execute_datetime_operations(self, executor):
        """Test datetime operations."""
        code = """
from datetime import datetime
dt = datetime(2024, 1, 1)
print(dt.year)
"""
        result = await executor.execute(code)
        assert result == "2024"

    @pytest.mark.asyncio
    async def test_execute_exception_handling(self, executor):
        """Test exception handling in code."""
        code = """
try:
    result = 10 / 2
except ZeroDivisionError:
    result = 0
print(result)
"""
        result = await executor.execute(code)
        assert result == "5.0"

    @pytest.mark.asyncio
    async def test_execute_class_definition(self, executor):
        """Test defining and using a class."""
        code = """
class Calculator:
    def add(self, a, b):
        return a + b

calc = Calculator()
print(calc.add(5, 3))
"""
        result = await executor.execute(code)
        assert result == "8"

    @pytest.mark.asyncio
    async def test_execute_with_return_value(self, executor):
        """Test code that has return statements but no print."""
        code = """
def add(a, b):
    return a + b

result = add(2, 3)
"""
        result = await executor.execute(code)
        assert result == "Script executed but produced no output"

    @pytest.mark.asyncio
    async def test_execute_large_output(self, executor):
        """Test code with large output."""
        code = 'print("x" * 1000)'
        result = await executor.execute(code)
        assert len(result) == 1000
        assert result == "x" * 1000

    @pytest.mark.asyncio
    async def test_execute_unicode(self, executor):
        """Test Unicode handling."""
        result = await executor.execute('print("Hello 世界 🌍")')
        assert result == "Hello 世界 🌍"

    @pytest.mark.asyncio
    async def test_execute_lambda(self, executor):
        """Test lambda function execution."""
        code = """
square = lambda x: x ** 2
print(square(5))
"""
        result = await executor.execute(code)
        assert result == "25"

    @pytest.mark.asyncio
    async def test_execution_is_stateless(self, executor):
        """Test that executions are stateless."""
        await executor.execute('x = 100')
        result = await executor.execute('print(x)')
        assert "NameError" in result
