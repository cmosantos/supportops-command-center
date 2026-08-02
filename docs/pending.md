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

## Gate

ST-04 is Done after independent QA PASS with zero open Critical/High/Medium
findings. The full regression passed with 192 tests and one environment-conditioned
Windows symlink skip. Version `0.4.0` is ready for its authorized local commit on
`main`; no Git remote is configured and Increment 5 has not started.
