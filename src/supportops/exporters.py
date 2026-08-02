# ruff: noqa: E501
"""Deterministic incident documentation serializers and contained writer."""

import hashlib
import json
import os
import re
import stat
from contextlib import suppress
from pathlib import Path
from uuid import uuid4

from supportops.domain.documentation import (
    ExportArtifact,
    ExportFormat,
    IncidentDocumentation,
    WrittenExport,
)
from supportops.errors import ConflictError, PersistenceError

HEADINGS = (
    ("Executive summary", "executive_summary"),
    ("Technical description", "technical_description"),
    ("Collected evidence", "collected_evidence"),
    ("Evaluated hypotheses", "evaluated_hypotheses"),
    ("Suggested procedures", "suggested_procedures"),
    ("Procedures actually performed", "performed_procedures"),
    ("Applied solution", "applied_solution"),
    ("Result and preventive recommendation", "result_and_preventive_recommendation"),
    ("GLPI/ServiceNow-ready text", "ticket_ready_text"),
)
SAFE_FILENAME = re.compile(r"^[a-z0-9][a-z0-9._-]{0,199}$")


def generated_filename(document: IncidentDocumentation, suffix: str) -> str:
    opaque = hashlib.sha256(document.incident_id.encode("utf-8")).hexdigest()[:16]
    return f"incident-{opaque}-r{document.revision:04d}.{suffix}"


def _inert(text: str) -> str:
    cleaned = "".join(
        char if char in "\n\t" or ord(char) >= 32 else "�" for char in text
    )
    escaped: list[str] = []
    for char in cleaned:
        if char == "<":
            escaped.append("&lt;")
        elif char == ">":
            escaped.append("&gt;")
        elif char in "\\`*_{}[]()#+-.!|~":
            escaped.append(f"\\{char}")
        else:
            escaped.append(char)
    return "".join(escaped)


def _is_reparse(path: Path) -> bool:
    metadata = path.lstat()
    attributes = getattr(metadata, "st_file_attributes", 0)
    return stat.S_ISLNK(metadata.st_mode) or bool(attributes & 0x400)


def _validate_existing_ancestors(path: Path) -> None:
    current = path.absolute()
    for candidate in (current, *current.parents):
        if candidate.exists() and _is_reparse(candidate):
            raise OSError


class MarkdownIncidentExporter:
    def export(self, documentation: IncidentDocumentation) -> ExportArtifact:
        parts: list[str] = []
        values = documentation.sections.model_dump()
        for heading, key in HEADINGS:
            value = values[key]
            if isinstance(value, tuple):
                rendered = "\n".join(f"- {_inert(str(item))}" for item in value)
            else:
                rendered = _inert(str(value))
            parts.append(f"## {heading}\n\n{rendered}")
        content = ("\n\n".join(parts) + "\n").encode("utf-8")
        return ExportArtifact(
            incident_id=documentation.incident_id,
            revision=documentation.revision,
            format=ExportFormat.MARKDOWN,
            media_type="text/markdown; charset=utf-8",
            filename=generated_filename(documentation, "md"),
            content=content,
        )


class JsonIncidentExporter:
    def export(self, documentation: IncidentDocumentation) -> ExportArtifact:
        payload = {
            "schema_version": "1",
            "incident_id": documentation.incident_id,
            "revision": documentation.revision,
            "generated_at": documentation.generated_at.isoformat(),
            "generated_by": documentation.generated_by,
            "sections": documentation.sections.model_dump(mode="json"),
        }
        content = (
            json.dumps(
                payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            + "\n"
        ).encode("utf-8")
        return ExportArtifact(
            incident_id=documentation.incident_id,
            revision=documentation.revision,
            format=ExportFormat.JSON,
            media_type="application/json; charset=utf-8",
            filename=generated_filename(documentation, "json"),
            content=content,
        )


class ContainedExportWriter:
    def __init__(self, root: Path) -> None:
        self.root = root

    def write(self, artifact: ExportArtifact) -> WrittenExport:
        if not SAFE_FILENAME.fullmatch(artifact.filename) or ".." in artifact.filename:
            raise PersistenceError("Export filename validation failed safely.")
        temporary: Path | None = None
        try:
            _validate_existing_ancestors(self.root)
            if self.root.exists() and (
                not self.root.is_dir() or self.root.is_symlink()
            ):
                raise OSError
            self.root.mkdir(parents=True, exist_ok=True)
            root = self.root.resolve(strict=True)
            target = (root / artifact.filename).resolve(strict=False)
            if target.parent != root:
                raise OSError
            if target.exists():
                raise ConflictError(
                    "Export already exists; existing files are preserved."
                )
            temporary = root / f".{uuid4().hex}.tmp"
            with temporary.open("xb") as stream:
                stream.write(artifact.content)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary, target)
        except ConflictError:
            raise
        except (OSError, ValueError):
            raise PersistenceError("Export write failed safely.") from None
        finally:
            if temporary is not None:
                with suppress(OSError):
                    temporary.unlink(missing_ok=True)
        return WrittenExport(
            incident_id=artifact.incident_id,
            revision=artifact.revision,
            format=artifact.format,
            media_type=artifact.media_type,
            filename=artifact.filename,
            relative_path=artifact.filename,
        )
