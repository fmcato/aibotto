"""
Base repository pattern for common database operations.

Consolidates repeated database access patterns across operations.py
"""

import contextlib
import logging
from collections.abc import Iterator
from typing import Any

from ..config.settings import Config

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository with common database operations."""

    @contextlib.contextmanager
    def _execute_db_operation(self) -> Iterator:
        """Context manager for database operations.

        Yields:
            Database cursor for operations

        Raises:
            Exception: Any database operation errors (with rollback)
        """
        conn = None
        try:
            import sqlite3

            conn = sqlite3.connect(Config.DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _save_record(
        self,
        table: str,
        columns: list[str],
        values: tuple,
        record_type: str = "record",
    ) -> int:
        """Generic save operation for database records.

        Args:
            table: Table name to insert into
            columns: List of column names
            values: Tuple of values matching columns
            record_type: Type label for logging

        Returns:
            ID of inserted record

        Raises:
            Exception: If database operation fails
        """
        try:
            with self._execute_db_operation() as cursor:
                placeholders = ", ".join(["?"] * len(columns))
                cols = ", ".join(columns)
                sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
                cursor.execute(sql, values)
                record_id = cursor.lastrowid
                logger.debug(f"Saved {record_type} {record_id}")
                return record_id
        except Exception as e:
            logger.error(f"Failed to save {record_type}: {e}")
            raise

    def _update_record(
        self,
        table: str,
        updates: dict[str, Any],
        where_clause: str,
        where_params: tuple,
    ) -> None:
        """Generic update operation for database records.

        Args:
            table: Table name to update
            updates: Dictionary of column: value pairs to update
            where_clause: SQL WHERE clause with ?
            where_params: Parameters for WHERE clause

        Raises:
            Exception: If database operation fails
        """
        try:
            with self._execute_db_operation() as cursor:
                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
                cursor.execute(sql, tuple(updates.values()) + where_params)
                logger.debug(f"Updated record in {table}")
        except Exception as e:
            logger.error(f"Failed to update in {table}: {e}")
            raise

    def _query_records(
        self,
        table: str,
        columns: list[str],
        where_clause: str | None = None,
        where_params: tuple = (),
    ) -> list[dict[str, Any]]:
        """Generic query operation for database records.

        Args:
            table: Table name to query
            columns: List of column names to select
            where_clause: Optional SQL condition (without WHERE keyword)
            where_params: Parameters for WHERE clause

        Returns:
            List of dictionaries with column names as keys

        Raises:
            Exception: If database operation fails
        """
        try:
            with self._execute_db_operation() as cursor:
                cols = ", ".join(columns)
                if where_clause:
                    sql = f"SELECT {cols} FROM {table} WHERE {where_clause}"
                else:
                    sql = f"SELECT {cols} FROM {table}"

                cursor.execute(sql, where_params)
                rows = cursor.fetchall()

                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to query {table}: {e}")
            raise

    def _query_single(
        self,
        table: str,
        columns: list[str],
        where_clause: str,
        where_params: tuple = (),
    ) -> dict[str, Any] | None:
        """Query a single record from database.

        Args:
            table: Table name to query
            columns: List of column names to select
            where_clause: SQL WHERE clause with ?
            where_params: Parameters for WHERE clause

        Returns:
            Dictionary with column names as keys, or None if not found

        Raises:
            Exception: If database operation fails
        """
        records = self._query_records(table, columns, where_clause, where_params)
        return records[0] if records else None

    def _delete_record(
        self,
        table: str,
        where_clause: str,
        where_params: tuple = (),
    ) -> None:
        """Delete records from database.

        Args:
            table: Table name to delete from
            where_clause: SQL WHERE clause with ?
            where_params: Parameters for WHERE clause

        Raises:
            Exception: If database operation fails
        """
        try:
            with self._execute_db_operation() as cursor:
                sql = f"DELETE FROM {table} WHERE {where_clause}"
                cursor.execute(sql, where_params)
                logger.debug(f"Deleted records from {table}")
        except Exception as e:
            logger.error(f"Failed to delete from {table}: {e}")
            raise

    def _execute_sql(self, sql: str, params: tuple = ()) -> None:
        """Execute custom SQL.

        Args:
            sql: SQL statement to execute
            params: Parameters for SQL statement

        Raises:
            Exception: If database operation fails
        """
        try:
            with self._execute_db_operation() as cursor:
                cursor.execute(sql, params)
                logger.debug(f"Executed SQL: {sql[:100]}...")
        except Exception as e:
            logger.error(f"Failed to execute SQL: {e}")
            raise
