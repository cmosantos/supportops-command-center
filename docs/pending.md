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

ST-03 is Done after independent QA PASS: 31/31 acceptance criteria and the full
150/150 regression passed. Version `0.3.0` is committed as `4ac772e` on the clean
`main` branch, with no Git remote configured. Increment 4 has not started and
remains blocked until explicit human approval after the final ST-03 report.
