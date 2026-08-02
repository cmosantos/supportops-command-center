# Roadmap

## Demonstrable offline V1

Increments 1–6 and 8 cover foundation, SQLite lifecycle, deterministic triage, lexical knowledge, persisted documentation/exports, Streamlit/dashboard, and hardening/delivery.

## Near-term product improvements

- Replace raw JSON triage entry with guided, schema-aware form controls.
- Return field-specific validation feedback without exposing internal traces.
- Add a deterministic synthetic data seeder for richer demonstrations and screenshots.
- Add English localization and multilingual runbook support.
- Improve dashboard visualizations while keeping metrics application-calculated and observational.

## Optional future evolution

- Increment 7: evaluate an optional local Ollama adapter behind a replaceable port. This is not part of V1, has no promised date, and must not weaken deterministic offline startup, validation, traceability, or no-execution controls.
- Calibrate triage using governed operational evidence.
- Define retention/redaction policy and authenticated actor integration.
- Evaluate ticket-system integration and SLA semantics under separate architecture, security, and product approval.
