# Pending Decisions and Work

## Product and governance

1. Security/Product must define a data-retention period. No automatic purge,
   physical deletion or fictional retention policy exists in V1.
2. Broader sensitive-data redaction guidance for future incident examples remains
   pending. ST-04 runbooks contain no credentials or personal data and follow the
   approved local authoring safety rules.
3. The approved initial triage policy must be calibrated in a future authorized
   increment using real operational data. Its conservative P2 concentration is a
   V1 safety decision, not a universal ITSM standard.
4. Governance is required before adding risk IDs, changing the 4x4 matrix or
   changing escalation/stop destinations; configuration changes are fail-closed.

## Implemented constraints retained

- Logically deleted incidents remain outside operational lifecycle and triage.
- Approver identity remains user-declared and unauthenticated.
- Re-triage snapshots are append-only and have no update/delete application API.
- Invalid triage policy configuration stops startup without a fallback.
- LLM/network providers, command execution, restore and physical deletion remain absent.
- Knowledge search is local, lexical, deterministic, read-only, and rooted in the
  packaged five-runbook corpus; it creates no authorization or execution path.
- Performed procedures are user-reported immutable facts, remain separate from
  suggestions/approvals, and never trigger execution.
- Documentation/export is persisted-only, revisioned, limited to Markdown/JSON,
  and contained beneath the configured application-owned export root.
- Streamlit is a thin presentation adapter over the shared Application façade;
  it owns no SQL, filesystem, scoring, serialization, or business policy.
- Incident category is explicit persisted input; it is never inferred from a
  triage matrix rule ID.

## Publication decisions still requiring a human

1. Select a definitive license after owner/legal review.
2. Choose repository owner, name, visibility, security contact, and whether
   container or package publication is desired.
3. Separately approve remote creation, branch protections, push, tag, and release;
   none was authorized or performed by this campaign.

## Gate

ST-08 completes local V1 `1.0.0` hardening after independent QA and DevOps PASS
with zero open Critical/High/Medium findings. Regression passed with 256 tests and
three environment-conditioned Windows skips. Clean CLI, Streamlit, Docker health,
SQLite/export persistence and recreation smokes passed. The local ST-08 commit is
the final campaign action on `main`; no remote or push is configured. Increment 7
remains optional, excluded, and unimplemented.
