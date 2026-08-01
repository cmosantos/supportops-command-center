import sqlite3
from pathlib import Path

import pytest

from supportops.errors import PersistenceError
from supportops.persistence.database import ConnectionFactory, MigrationRunner
from supportops.persistence.migrations import MIGRATIONS, Migration


def factory(path: Path) -> ConnectionFactory:
    return ConnectionFactory(path, 200)


def test_status_nonexistent_is_non_mutating_and_init_is_idempotent(
    tmp_path: Path,
) -> None:
    path = tmp_path / "supportops.db"
    runner = MigrationRunner(factory(path))

    assert runner.status() == (0, (1,))
    assert not path.exists()
    assert runner.apply("2026-08-01T00:00:00+00:00") == 1
    assert runner.apply("2026-08-01T00:00:01+00:00") == 0
    assert runner.status() == (1, ())

    connection = factory(path).connect()
    try:
        assert (
            connection.execute("SELECT count(*) FROM schema_migrations").fetchone()[0]
            == 1
        )
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 200
    finally:
        connection.close()


def test_checksum_drift_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "drift.db"
    runner = MigrationRunner(factory(path))
    runner.apply("2026-08-01T00:00:00+00:00")
    connection = factory(path).connect()
    connection.execute(
        "UPDATE schema_migrations SET checksum = ? WHERE version = ?", ("0" * 64, 1)
    )
    connection.close()

    with pytest.raises(PersistenceError):
        runner.apply("2026-08-01T00:00:01+00:00")


def test_missing_or_unordered_migration_sequence_is_rejected(tmp_path: Path) -> None:
    invalid = (Migration(2, "gap", ("CREATE TABLE gap(id INTEGER)",)),)
    runner = MigrationRunner(factory(tmp_path / "gap.db"), invalid)

    with pytest.raises(PersistenceError):
        runner.apply("2026-08-01T00:00:00+00:00")


def test_migration_failure_rolls_back_schema_and_ledger(tmp_path: Path) -> None:
    broken = (
        MIGRATIONS[0],
        Migration(2, "broken", ("CREATE TABLE partial(id INTEGER)", "INVALID SQL")),
    )
    path = tmp_path / "broken.db"

    with pytest.raises(PersistenceError):
        MigrationRunner(factory(path), broken).apply("2026-08-01T00:00:00+00:00")

    connection = sqlite3.connect(path)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert "partial" not in tables
        assert "incidents" not in tables
        assert "schema_migrations" not in tables
    finally:
        connection.close()


def test_foreign_key_rejects_orphan_event_and_rolls_back(tmp_path: Path) -> None:
    path = tmp_path / "foreign-key.db"
    configured = factory(path)
    MigrationRunner(configured).apply("2026-08-01T00:00:00+00:00")
    connection = configured.connect()
    try:
        connection.execute("BEGIN IMMEDIATE")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO incident_events(id,incident_id,sequence,event_type,"
                "occurred_at,details_json) VALUES (?,?,?,?,?,?)",
                (
                    "event-orphan",
                    "missing-incident",
                    1,
                    "TEST",
                    "2026-08-01T00:00:00+00:00",
                    "{}",
                ),
            )
        connection.rollback()
        assert (
            connection.execute("SELECT count(*) FROM incident_events").fetchone()[0]
            == 0
        )
    finally:
        connection.close()
