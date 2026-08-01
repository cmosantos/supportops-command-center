# Pending Decisions and Work

## Required before related implementation

1. Support Specialist must publish the complete 4x4 impact/urgency matrix and
   boundary cases consistent with the approved P1-P4 guidance.
2. Product Owner must approve the canonical future story breakdown ST-01–ST-16.
3. Security/Product must define a data-retention period; no retention/deletion job
   is inferred in V1.
4. Technical Writer/Support Specialist must define safe redaction guidance for
   example incident data and runbooks.

## Architecture semantics resolved in Phase 2

- Logically deleted incidents are excluded from normal lists, dashboard metrics,
  and normal exports; preserved records are available only through an explicit
  internal audit repository query. V1 exposes no restore or audit export UI.
- Approver identity is a user-supplied reference, not authenticated identity. Each
  decision binds to the exact action ID, version, digest, and snapshot.
- Invalid/incomplete priority configuration fails startup closed with a safe error;
  the system does not silently substitute hard-coded rules.

## Gate

Phase 2 was approved. ST-01 is the only authorized Phase 3 increment. Increment 2, SQLite, triage, Streamlit, runbooks, and Ollama remain blocked pending new human approval.

The Support Specialist 4x4 policy remains pending; ST-01 validates structure only and performs no classification.

