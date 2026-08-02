# Security Policy

## Supported versions

Until publication, only the current `main` branch is intended for security fixes.
The future maintainer must publish an explicit supported-version table.

## Report a vulnerability

Do not open a public issue containing exploit details, credentials, incident data
or personal information. Before publication, contact the project owner through a
private channel agreed directly with them. A real security address must be chosen
and inserted during the GitHub publication checklist; no nonexistent address is
advertised here.

Include affected version/commit, reproducible synthetic steps, impact, and any
safe mitigation. Never test against real service-desk or Microsoft 365 data.

## Threat and trust boundaries

SupportOps is a local single-user demonstration, not an authentication or remote
administration system. Actor names are operator-declared. The application never
executes suggested commands or administrative actions. It has no LLM/provider or
ticket-system integration and requires no outbound product service.

SQLite and export directories are trusted application-owned roots. Operators are
responsible for host access controls, backups, Docker volume protection and the
content entered into incidents. Do not enter secrets. Review generated exports
before sharing and treat them as potentially sensitive operational records.

Security controls reduce risk but are not a guarantee. Keep Python/container
dependencies patched, use loopback exposure for local demos, and run the documented
quality/scanning gates before publication.
