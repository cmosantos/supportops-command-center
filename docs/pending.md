# Pending Decisions and Work

## Product and governance

1. Security/Product must define a data-retention period. No automatic purge,
   physical deletion or fictional retention policy exists in V1.
2. Technical Writer/Support Specialist must define safe redaction guidance for
   future example incident data and runbooks.
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
- Streamlit, runbook search, hypotheses, troubleshooting plans, LLM/network
  providers, command execution, restore and physical deletion remain absent.

## Gate

ST-03 implementation is in independent QA review. Increment 4 remains blocked
until explicit human approval after the final ST-03 report.
