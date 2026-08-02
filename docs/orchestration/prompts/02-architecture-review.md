# Architecture Review Prompt

```text
Review the proposed architecture as independent architect, security critic, and operations reviewer.

Evaluate:
- dependency direction and replaceable ports;
- data model, migrations, audit/history, concurrency, and rollback;
- trust boundaries, secrets, PII, path handling, SQL, network, and command execution;
- deterministic/offline fallback behavior;
- CLI, UI, packaging, Docker, observability, and testability;
- requirements-to-stories-to-tests traceability;
- irreversible decisions and future migration paths.

Classify findings as Critical, High, Medium, or Low.
Block implementation for unresolved Critical/High findings.
Record accepted decisions as ADRs.
Return the smallest safe increment plan and explicit human decisions.
Do not implement code during this review.
```
