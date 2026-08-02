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
- Streamlit, hypotheses, troubleshooting plans, LLM/network providers, command
  execution, restore and physical deletion remain absent.
- Knowledge search is local, lexical, deterministic, read-only, and rooted in the
  packaged five-runbook corpus; it creates no authorization or execution path.
- Performed procedures are user-reported immutable facts, remain separate from
  suggestions/approvals, and never trigger execution.
- Documentation/export is persisted-only, revisioned, limited to Markdown/JSON,
  and contained beneath the configured application-owned export root.

## Gate

ST-05 is Done after independent QA PASS with zero open Critical/High/Medium
findings. The full regression passed with 218 tests and two environment-conditioned
Windows symlink skips. Version `0.5.0` is ready for its authorized local commit on
`main`; no Git remote is configured. Increment 6 follows automatically under the
approved final V1 campaign; Increment 7 remains optional and excluded.
