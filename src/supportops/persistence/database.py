"""SQLite connection, migration, and transaction management."""

import sqlite3
from collections.abc import Iterator
from contextlib import AbstractContextManager
from pathlib import Path
from types import TracebackType

from supportops.errors import PersistenceError
from supportops.persistence.migrations import (
    MIGRATIONS,
    Migration,
    validate_migration_sequence,
)


class ConnectionFactory:
    def __init__(self, path: Path, busy_timeout_ms: int) -> None:
        self.path = path
        self.busy_timeout_ms = busy_timeout_ms

    def connect(self) -> sqlite3.Connection:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(
                self.path, timeout=self.busy_timeout_ms / 1000, isolation_level=None
            )
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms:d}")
            connection.execute("PRAGMA journal_mode = WAL")
            return connection
        except (OSError, sqlite3.Error):
            raise PersistenceError("Database connection failed safely.") from None


class MigrationRunner:
    LEDGER_SQL = """CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        description TEXT NOT NULL,
        applied_at TEXT NOT NULL,
        checksum TEXT NOT NULL
    )"""

    def __init__(
        self, factory: ConnectionFactory, migrations: tuple[Migration, ...] = MIGRATIONS
    ) -> None:
        self.factory = factory
        self.migrations = migrations

    def status(self) -> tuple[int, tuple[int, ...]]:
        validate_migration_sequence(self.migrations)
        if not self.factory.path.exists():
            return 0, tuple(m.version for m in self.migrations)
        connection = self.factory.connect()
        try:
            exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = ? AND name = ?",
                ("table", "schema_migrations"),
            ).fetchone()
            if not exists:
                return 0, tuple(m.version for m in self.migrations)
            rows = connection.execute(
                "SELECT version, checksum FROM schema_migrations ORDER BY version"
            ).fetchall()
            self._verify_applied(rows)
            applied = {int(row["version"]) for row in rows}
            return max(applied, default=0), tuple(
                m.version for m in self.migrations if m.version not in applied
            )
        except (sqlite3.Error, ValueError):
            raise PersistenceError(
                "Migration status validation failed safely."
            ) from None
        finally:
            connection.close()

    def apply(self, applied_at: str) -> int:
        try:
            validate_migration_sequence(self.migrations)
        except ValueError:
            raise PersistenceError("Migration sequence is invalid.") from None
        connection = self.factory.connect()
        applied_count = 0
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(self.LEDGER_SQL)
            rows = connection.execute(
                "SELECT version, checksum FROM schema_migrations ORDER BY version"
            ).fetchall()
            self._verify_applied(rows)
            applied = {int(row["version"]) for row in rows}
            for migration in self.migrations:
                if migration.version in applied:
                    continue
                for statement in migration.statements:
                    connection.execute(statement)
                connection.execute(
                    "INSERT INTO schema_migrations("
                    "version, description, applied_at, checksum) VALUES (?, ?, ?, ?)",
                    (
                        migration.version,
                        migration.description,
                        applied_at,
                        migration.checksum,
                    ),
                )
                applied_count += 1
            connection.commit()
            return applied_count
        except (sqlite3.Error, ValueError):
            connection.rollback()
            raise PersistenceError("Database migration failed safely.") from None
        finally:
            connection.close()

    def _verify_applied(self, rows: list[sqlite3.Row]) -> None:
        known = {migration.version: migration for migration in self.migrations}
        versions = [int(row["version"]) for row in rows]
        if versions and versions != list(range(1, max(versions) + 1)):
            raise ValueError("applied migration sequence has gaps")
        for row in rows:
            version = int(row["version"])
            if version not in known or row["checksum"] != known[version].checksum:
                raise ValueError("migration checksum drift")


class UnitOfWork(AbstractContextManager["UnitOfWork"]):
    def __init__(self, factory: ConnectionFactory) -> None:
        self.factory = factory
        self.connection: sqlite3.Connection | None = None
        self._committed = False

    def __enter__(self) -> "UnitOfWork":
        self.connection = self.factory.connect()
        try:
            self.connection.execute("BEGIN IMMEDIATE")
        except sqlite3.Error:
            self.connection.close()
            self.connection = None
            raise PersistenceError(
                "Database transaction could not start safely."
            ) from None
        return self

    @property
    def active_connection(self) -> sqlite3.Connection:
        if self.connection is None:
            raise RuntimeError("unit of work is not active")
        return self.connection

    def commit(self) -> None:
        if self.connection is None:
            raise RuntimeError("unit of work is not active")
        self.connection.commit()
        self._committed = True

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.connection is not None:
            if exc_type is not None or not self._committed:
                self.connection.rollback()
            self.connection.close()
            self.connection = None
        return None


def rows(
    connection: sqlite3.Connection, sql: str, values: tuple[object, ...] = ()
) -> Iterator[sqlite3.Row]:
    yield from connection.execute(sql, values)
