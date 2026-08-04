# Roadmap

## Demonstrable offline V1

Increments 1–6 and 8 cover foundation, SQLite lifecycle, deterministic triage, lexical knowledge, persisted documentation and exports, Streamlit and dashboard delivery, plus hardening.

The Streamlit presentation, repository documentation, and packaged operational runbooks are maintained in English. Presentation text remains isolated from domain rules so interface wording can evolve without changing deterministic triage behavior.

## Near-term product improvements

- Replace raw JSON triage entry with guided, schema-aware form controls.
- Return field-specific validation feedback without exposing internal traces.
- Add a deterministic synthetic data seeder for richer demonstrations and screenshots.
- Improve English runbook coverage and knowledge-search relevance.
- Improve dashboard visualizations while keeping metrics application-calculated and observational.

## Optional future evolution

- Increment 7: evaluate an optional local Ollama adapter behind a replaceable port. This is not part of V1, has no promised date, and must not weaken deterministic offline startup, validation, traceability, or no-execution controls.
- Calibrate triage using governed operational evidence.
- Define retention and redaction policy plus authenticated actor integration.
- Evaluate ticket-system integration and SLA semantics under separate architecture, security, and product approval.
