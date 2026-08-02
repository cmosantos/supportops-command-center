"""Clean-root SQLite integrity and restart validation."""

from pathlib import Path

from supportops.config import Settings
from supportops.domain.incidents import IncidentCreate
from supportops.domain.priority_matrix import Impact, Urgency
from supportops.lifecycle import IncidentService
from supportops.persistence.database import ConnectionFactory, MigrationRunner


def test_clean_database_is_idempotent_integral_and_reopens(tmp_path: Path) -> None:
    database = tmp_path / "runtime" / "supportops.db"
    settings = Settings(db_path=database, export_root=tmp_path / "exports")
    factory = ConnectionFactory(settings.db_path, settings.db_busy_timeout_ms)
    migrations = MigrationRunner(factory)
    assert migrations.status() == (0, (1, 2, 3, 4))
    assert not database.exists()
    assert migrations.apply("2026-08-02T00:00:00+00:00") == 4
    assert migrations.apply("2026-08-02T00:00:01+00:00") == 0

    incident = IncidentService(factory).create(
        IncidentCreate(
            title="Synthetic clean runtime",
            description="Demonstration record",
            affected_party="Example User",
            affected_service="Example Service",
            impact=Impact.LOW,
            urgency=Urgency.LOW,
            symptoms="Synthetic symptom",
        )
    )
    reopened = IncidentService(ConnectionFactory(database, 5000)).get(incident.id)
    assert reopened.title == incident.title

    connection = factory.connect()
    try:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        connection.close()
