"""
Tests for BaseRepository pattern for database operations.
"""

import json
import os
import sqlite3
import tempfile

import pytest

from src.aibotto.config.settings import Config
from src.aibotto.db.base_repository import BaseRepository


class TestBaseRepository:
    """Test BaseRepository database operations."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        original_db_path = Config.DATABASE_PATH
        Config.DATABASE_PATH = db_path

        yield db_path

        Config.DATABASE_PATH = original_db_path
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def base_repository(self, temp_db):
        """Create BaseRepository instance with test database."""
        return BaseRepository()

    def test_execute_db_operation_context_manager(self, base_repository):
        """Test database operation context manager."""
        with base_repository._execute_db_operation() as cursor:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)"
            )

        with base_repository._execute_db_operation() as cursor:
            result = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = result.fetchall()
            assert len(tables) >= 1

    def test_execute_db_operation_commit_on_success(self, base_repository):
        """Test changes are committed on successful operation."""
        with base_repository._execute_db_operation() as cursor:
            cursor.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)"
            )
            cursor.execute("INSERT INTO test_table (value) VALUES (?)", ("test",))

        with base_repository._execute_db_operation() as cursor:
            result = cursor.execute("SELECT value FROM test_table")
            values = result.fetchall()
            assert len(values) == 1
            assert values[0][0] == "test"

    def test_execute_db_operation_rollback_on_error(self, base_repository):
        """Test changes are rolled back on error."""
        with base_repository._execute_db_operation() as cursor:
            cursor.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)"
            )

        try:
            with base_repository._execute_db_operation() as cursor:
                cursor.execute("INSERT INTO test_table (value) VALUES (?)", ("test1",))
                raise ValueError("Simulated error")
        except ValueError:
            pass

        with base_repository._execute_db_operation() as cursor:
            result = cursor.execute("SELECT COUNT(*) FROM test_table")
            count = result.fetchone()[0]
            assert count == 0

    def test_save_record_basic(self, base_repository):
        """Test basic record save operation."""
        with base_repository._execute_db_operation() as cursor:
            cursor.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)"
            )

        record_id = base_repository._save_record(
            "test_table",
            ["name", "value"],
            ("test_name", 42),
            "test_record",
        )

        assert record_id > 0

        with base_repository._execute_db_operation() as cursor:
            result = cursor.execute("SELECT id, name, value FROM test_table WHERE id = ?", (record_id,))
            record = result.fetchone()
            assert record is not None
            assert record[1] == "test_name"
            assert record[2] == 42

    def test_save_record_with_json_metadata(self, base_repository):
        """Test record save with JSON metadata."""
        with base_repository._execute_db_operation() as cursor:
            cursor.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT, metadata TEXT)"
            )

        metadata = {"key": "value", "nested": {"data": 123}}
        record_id = base_repository._save_record(
            "test_table",
            ["name", "metadata"],
            ("test_record", json.dumps(metadata)),
            "test_record_with_metadata",
        )

        assert record_id > 0

        with base_repository._execute_db_operation() as cursor:
            result = cursor.execute("SELECT metadata FROM test_table WHERE id = ?", (record_id,))
            stored_metadata = json.loads(result.fetchone()[0])
            assert stored_metadata == metadata

    def test_update_record_basic(self, base_repository):
        """Test basic record update operation."""
        with base_repository._execute_db_operation() as cursor:
            cursor.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)"
            )
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("original", 10))

        base_repository._update_record(
            "test_table",
            {"name": "updated", "value": 20},
            "id = 1",
            (),
        )

        with base_repository._execute_db_operation() as cursor:
            result = cursor.execute("SELECT name, value FROM test_table WHERE id = 1")
            record = result.fetchone()
            assert record[0] == "updated"
            assert record[1] == 20

    def test_update_record_with_where_params(self, base_repository):
        """Test record update with WHERE clause parameters."""
        with base_repository._execute_db_operation() as cursor:
            cursor.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)"
            )
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test1", 10))
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test2", 20))

        base_repository._update_record(
            "test_table",
            {"value": 100},
            "name = ?",
            ("test1",),
        )

        with base_repository._execute_db_operation() as cursor:
            result = cursor.execute("SELECT name, value FROM test_table ORDER BY name")
            records = result.fetchall()
            assert records[0][1] == 100  # test1 updated
            assert records[1][1] == 20  # test2 unchanged

    def test_query_record_basic(self, base_repository):
        """Test basic record query operation."""
        with base_repository._execute_db_operation() as cursor:
            cursor.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)"
            )
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test1", 10))
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test2", 20))

        result = base_repository._query_records(
            "test_table",
            ["id", "name", "value"],
            "name = ?",
            ("test1",),
        )

        assert len(result) == 1
        assert result[0]["name"] == "test1"
        assert result[0]["value"] == 10

    def test_query_record_all(self, base_repository):
        """Test querying all records without WHERE clause."""
        with base_repository._execute_db_operation() as cursor:
            cursor.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)"
            )
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test1", 10))
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test2", 20))
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test3", 30))

        result = base_repository._query_records(
            "test_table",
            ["id", "name", "value"],
        )

        assert len(result) == 3
        assert result[0]["name"] == "test1"
        assert result[1]["name"] == "test2"
        assert result[2]["name"] == "test3"

    def test_query_record_single(self, base_repository):
        """Test querying single record."""
        with base_repository._execute_db_operation() as cursor:
            cursor.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)"
            )
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test1", 10))
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test2", 20))

        result = base_repository._query_single(
            "test_table",
            ["name", "value"],
            "id = ?",
            (1,),
        )

        assert result is not None
        assert result["name"] == "test1"
        assert result["value"] == 10

    def test_query_record_single_not_found(self, base_repository):
        """Test querying single record that doesn't exist."""
        with base_repository._execute_db_operation() as cursor:
            cursor.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)"
            )

        result = base_repository._query_single(
            "test_table",
            ["name", "value"],
            "id = ?",
            (999,),
        )

        assert result is None

    def test_delete_record(self, base_repository):
        """Test record deletion."""
        with base_repository._execute_db_operation() as cursor:
            cursor.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)"
            )
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test1", 10))
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test2", 20))

        base_repository._delete_record(
            "test_table",
            "id = ?",
            (1,),
        )

        with base_repository._execute_db_operation() as cursor:
            result = cursor.execute("SELECT COUNT(*) FROM test_table")
            count = result.fetchone()[0]
            assert count == 1

    def test_execute_sql(self, base_repository):
        """Test custom SQL execution."""
        with base_repository._execute_db_operation() as cursor:
            cursor.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)"
            )

        base_repository._execute_sql(
            "INSERT INTO test_table (name, value) VALUES (?, ?), (?, ?)",
            ("test1", 10, "test2", 20),
        )

        with base_repository._execute_db_operation() as cursor:
            result = cursor.execute("SELECT COUNT(*) FROM test_table")
            count = result.fetchone()[0]
            assert count == 2

    def test_execute_sql_with_logging(self, base_repository, caplog):
        """Test SQL execution with debug logging."""
        with base_repository._execute_db_operation() as cursor:
            cursor.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)"
            )

        with caplog.at_level("DEBUG"):
            base_repository._execute_sql("INSERT INTO test_table (name) VALUES (?)", ("test",))

        assert any("Executed SQL" in record.message for record in caplog.records)