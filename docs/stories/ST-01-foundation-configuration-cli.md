# ST-01 — Foundation, Configuration and CLI

## Status

**Ready**

## Objective

Create the minimal, secure, testable Python 3.12 foundation for SupportOps Command
Center: package metadata, validated configuration, a structural priority-matrix
contract, safe errors, redacted logging, a composition root, and the CLI commands
`version`, `config validate`, and `doctor`.

The increment must work without LLM, network, database, or external services.

## Scope

### In scope

- Python package and one canonical version source.
- Pydantic Settings with safe defaults and optional local `.env`.
- Structural, configurable 4x4 impact/urgency matrix model; no incident triage.
- Safe public error messages and recursive sensitive-field redaction.
- Minimal contracts and composition root.
- Standard-library `argparse` CLI.
- Unit, contract, CLI, security, and smoke tests.
- Usage and evidence documentation.

### Out of scope

SQLite, incidents, triage decisions, Support Specialist boundary rules, runbooks,
knowledge search, Streamlit, Ollama/OpenAI adapters, HTTP/network calls, exports,
dashboard, Docker, and every form of shell or external-command execution.

## Architecture and security constraints

1. CLI First; no UI.
2. No `subprocess`, `os.system`, `os.popen`, shell option, `exec`, `eval`,
   or dynamic import based on user input.
3. `doctor` performs in-process checks only.
4. No passwords, tokens, API keys, authorization values, or secrets in output/logs.
5. LLM remains disabled by default and no LLM adapter is introduced.
6. No initialization access to network, SQLite, Streamlit, Ollama, or runbooks.
7. All changes remain inside this isolated repository.

## Acceptance Criteria

1. Project requires Python >=3.12,<3.13 and the package installs/imports.
2. One version source drives both package and `supportops version`; exit code 0.
3. Pydantic Settings loads safe defaults without `.env` and supports environment
   overrides using the documented prefix.
4. LLM is disabled by default; the story runs without LLM/network/credentials.
5. `.env.example` contains safe examples and `.env` remains ignored.
6. Invalid settings produce actionable public errors without stack traces or values.
7. Matrix contract accepts only Impact/Urgency enums and P1-P4, rejects extras.
8. Matrix contract rejects missing/conflicting combinations and performs no triage.
9. CLI uses services built by the composition root, not embedded matrix rules.
10. Logging redacts password, token, secret, api_key, and authorization recursively.
11. Unexpected CLI errors map to a generic safe message and non-zero exit code.
12. Composition root imports no SQLite, Streamlit, Ollama, or network client.
13. `config validate` returns 0 when valid and non-zero when invalid.
14. `doctor` reports Python, settings, matrix contract, logging, and composition-root
    checks using in-process operations and coherent exit codes.
15. Automated static test rejects prohibited execution APIs in application source.
16. Unit, contract, CLI, security, and smoke tests pass offline.
17. Ruff, MyPy, Pytest, package build/install, and manual CLI demonstrations pass.
18. Final diff contains only files in this isolated project.

## Tasks

- [ ] Confirm repository isolation, baseline, and ignore rules.
- [ ] Create package metadata, Python 3.12 constraint, dependencies, and entry point.
- [ ] Implement typed settings and safe configuration errors.
- [ ] Implement Impact/Urgency/Priority and structural matrix validation only.
- [ ] Implement safe error hierarchy and recursive logging redaction.
- [ ] Implement minimal contracts, diagnostics, version provider, and composition root.
- [ ] Implement `version`, `config validate`, and `doctor`.
- [ ] Add unit, contract, CLI, security, and smoke tests.
- [ ] Update README, progress, pending items, evidence, and File List.
- [ ] Run all quality gates and fix every failure.
- [ ] Complete DoD self-review and request QA review.

## Planned tests

- Settings defaults, env override, invalid values, safe errors, LLM disabled.
- Complete/partial/extra/invalid priority-matrix structures without classification.
- Recursive sensitive-key redaction and preservation of safe fields.
- Contract conformance for settings/version/diagnostics/composition root.
- CLI success/failure exit codes and safe output.
- Import/bootstrap/three-command smoke tests with network blocked.
- AST/static scan for prohibited execution APIs and forbidden adapter imports.

## Dependencies

Runtime: Pydantic and Pydantic Settings. Development: Pytest, Ruff, MyPy, and build.
CLI uses standard-library argparse. No SQLite, Streamlit, HTTP, or LLM dependency.

## Risks

- Structural matrix accidentally becomes a triage engine: keep it validation-only.
- Settings/log errors leak values: normalize to safe public messages and test.
- Doctor becomes an external command runner: in-process checks only.
- Composition root imports future adapters: enforce with source/import tests.
- Tooling unavailable in the local Python environment: create an isolated project
  virtual environment and record exact installation/test evidence.

## Dev Agent Record

### Agent

### Model

### Started At

### Completed At

### Implementation Notes

### Debug Log References

### Completion Notes

### Quality Gate Results

### Evidence References

### Change Log

| Date | Version | Change | Agent |
|---|---|---|---|

## File List

Planned; the development agent must replace this with the actual list.

- `pyproject.toml`
- `src/supportops/**`
- `tests/**`
- `README.md`
- `.env.example`
- `docs/progress.md`
- `docs/pending.md`
- `docs/stories/ST-01-foundation-configuration-cli.md`
