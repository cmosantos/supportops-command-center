import os
from pathlib import Path

import pytest

from supportops.domain.documentation import ExportArtifact, ExportFormat
from supportops.errors import PersistenceError
from supportops.exporters import ContainedExportWriter


@pytest.mark.parametrize(
    "filename",
    ["../escape.json", "C:\\escape.json", "/escape.json", "a/b.json", "..json"],
)
def test_writer_rejects_traversal_and_absolute_names(
    tmp_path: Path, filename: str
) -> None:
    artifact = ExportArtifact(
        incident_id="i",
        revision=1,
        format=ExportFormat.JSON,
        media_type="application/json",
        filename=filename,
        content=b"{}",
    )
    with pytest.raises(PersistenceError):
        ContainedExportWriter(tmp_path / "exports").write(artifact)
    assert not (tmp_path / "escape.json").exists()


def test_file_valued_root_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.write_text("not a directory")
    artifact = ExportArtifact(
        incident_id="i",
        revision=1,
        format=ExportFormat.JSON,
        media_type="application/json",
        filename="safe.json",
        content=b"{}",
    )
    with pytest.raises(PersistenceError):
        ContainedExportWriter(root).write(artifact)


def artifact() -> ExportArtifact:
    return ExportArtifact(
        incident_id="i",
        revision=1,
        format=ExportFormat.JSON,
        media_type="application/json",
        filename="safe.json",
        content=b"{}",
    )


@pytest.mark.parametrize("operation", ["fsync", "link"])
def test_failed_publication_cleans_temporary_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, operation: str
) -> None:
    root = tmp_path / "exports"
    if operation == "fsync":
        monkeypatch.setattr(os, "fsync", lambda _: (_ for _ in ()).throw(OSError()))
    else:
        monkeypatch.setattr(os, "link", lambda *_: (_ for _ in ()).throw(OSError()))
    with pytest.raises(PersistenceError):
        ContainedExportWriter(root).write(artifact())
    assert list(root.glob(".*.tmp")) == []
    assert not (root / "safe.json").exists()


def test_failed_write_cleans_temporary_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    original = Path.open

    class FailingFile:
        def __init__(self, stream: object) -> None:
            self.stream = stream

        def __enter__(self) -> "FailingFile":
            self.stream.__enter__()  # type: ignore[attr-defined]
            return self

        def __exit__(self, *args: object) -> object:
            return self.stream.__exit__(*args)  # type: ignore[attr-defined]

        def write(self, _: bytes) -> int:
            raise OSError

    def failing_open(path: Path, *args: object, **kwargs: object) -> object:
        stream = original(path, *args, **kwargs)  # type: ignore[call-overload]
        return FailingFile(stream) if path.name.endswith(".tmp") else stream

    monkeypatch.setattr(Path, "open", failing_open)
    root = tmp_path / "exports"
    with pytest.raises(PersistenceError):
        ContainedExportWriter(root).write(artifact())
    assert list(root.glob(".*.tmp")) == []


def test_symlink_ancestor_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    parent = tmp_path / "linked"
    try:
        parent.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(PersistenceError):
        ContainedExportWriter(parent / "exports").write(artifact())
    assert list(outside.rglob("*")) == []
