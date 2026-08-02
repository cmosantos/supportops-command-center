# SupportOps deterministic triage policy

Status: Approved initial V1 and implemented by ST-03
Policy ID: `supportops-triage`
Schema version: `1`
Matrix version: `2026.08-v1`
Owner: Support Specialist N1/N2

This document is the operational source of truth implemented by Increment 3. It
remains an initial V1 subject to future calibration with real operational data.
The conservative concentration of cells in P2 is a deliberate V1 safety decision,
not a universal ITSM standard.

## Purpose and invariants

The policy classifies an incident from two independently assessed dimensions:
impact and urgency. The 4x4 lookup determines priority. Separate deterministic
rules determine support level, escalation, evidence gaps, and whether
troubleshooting must stop.

1. Priority is never inferred from title, category, requester seniority, pressure,
   or the support analyst's discretion alone.
2. Impact and urgency must each have evidence. If either is unknown or
   contradictory, classification is incomplete and blocking questions are shown.
3. P1 is reserved for `critical impact + critical urgency`.
4. A high impact or high urgency produces at least P2. A critical value also
   produces at least P2, even when the other dimension is lower.
5. P3 covers moderate operational exposure without a critical/high dimension.
   P4 is reserved for low impact and low urgency.
6. Priority does not authorize an action, promise an SLA, or execute a command.
7. Escalation can be stricter than the matrix when a universal escalation trigger
   applies. It may never reduce the matrix priority.
8. Invalid, incomplete, duplicate, unknown, or unreadable policy configuration
   fails closed at startup. There is no embedded or silent fallback matrix.
9. Each triage result records policy ID, schema version, matrix version, normalized
   inputs, matched rule ID, rationale, evidence gaps, support recommendation, and
   escalation outcome.

## Impact criteria

Assess current or credibly imminent business reach and consequence, not how soon
the requester wants action. When multiple criteria apply, use the highest supported
level. Forecasts must identify their evidence source.

| Impact | Objective criteria | Minimum evidence | Boundary guidance |
|---|---|---|---|
| `low` | One user or one non-critical endpoint/function; no shared service outage; negligible business loss; viable workaround preserves the essential task. | Affected user/device, service/function, confirmation that the workaround works, and absence of wider reports. | One executive user is not automatically higher impact. Raise the level only when an evidenced business process or broader population is affected. |
| `moderate` | Multiple users within one team or location, or a relevant business function is degraded; work continues through a viable but costly/manual workaround; no enterprise-wide or critical-process halt. | Estimated affected count/scope, degraded function, workaround and its operational cost, and affected location/team. | A single user can be moderate when that user is the sole operator of an evidenced important process. A vague claim of “many users” remains unconfirmed. |
| `high` | Department, multiple teams/locations, or a critical service is materially degraded; substantial productivity loss; workaround is limited, unstable, or unavailable for an important process. | Population/scope from at least one reliable source, service condition, business process affected, and workaround assessment. | A critical service with isolated cosmetic degradation is not high. A small population can be high if a documented critical business process is stopped. |
| `critical` | Enterprise/widespread outage; active safety, security, privacy, regulatory, or data-integrity consequence; or complete halt of a mission-critical process with material and continuing loss. | Corroborated scope or authoritative alert, consequence being incurred, critical process/asset, and containment/workaround status. | Potential severity alone is insufficient when exposure is contained and no critical process is stopped. Active compromise, unsafe condition, or continuing data corruption remains critical even with a small observed population. |

## Urgency criteria

Assess how quickly harm materially increases if action is delayed. These response
bands guide ordering only; they are not contractual SLA commitments.

| Urgency | Objective criteria | Minimum evidence | Boundary guidance |
|---|---|---|---|
| `low` | Stable condition; effective workaround; no material deadline in the current operating window; action can be scheduled without meaningful additional harm. | Workaround validation, relevant deadline, condition stability, and acceptable work window. | Requester preference for “today” does not raise urgency without an evidenced consequence of delay. |
| `moderate` | Ongoing degradation or recurring interruption; workaround exists but adds meaningful effort; action is needed in the normal/next business window to avoid accumulating impact. | Failure frequency, workaround burden, next relevant deadline, and trend. | A long-open but stable incident is not automatically high urgency; use current rate of harm. |
| `high` | Material deadline or operating window is within hours/current shift; workaround is fragile or capacity-limited; delay is likely to cause significant disruption soon. | Time and owner of the deadline, expected consequence, workaround capacity, and time-to-harm. | “Urgent” without a time-to-harm remains unconfirmed. A scheduled event can be high even before impact expands. |
| `critical` | Immediate intervention is needed because harm is active or rapidly increasing, no viable containment/workaround exists, or a safety/security/data-integrity/mission-critical deadline is being breached now. | Current time-sensitive consequence, containment status, workaround failure, and authoritative alert or corroboration where available. | A future major deadline is high until the immediate-harm condition is met. Active compromise, unsafe operation, or continuing corruption is critical urgency. |

## Complete 4x4 priority matrix

Legend for baseline routing: **N1** means N1 owns evidence collection and safe,
documented checks; **N2** means N2 ownership is recommended. **Mandatory** escalation
must be recorded immediately; **conditional** escalation depends on the deterministic
triggers below; **none** means no baseline escalation, while universal triggers
still apply.

| Rule | Impact | Urgency | Priority | Justification | Practical example | Boundary / evidence condition | Baseline routing | Planned test |
|---|---|---|---|---|---|---|---|---|
| `MX-LL` | low | low | P4 | Isolated, stable and safely deferrable. | One user has a cosmetic Outlook view issue and a working alternate view. | If the alternate path does not preserve the essential task, reassess urgency. Confirm no wider reports. | N1; no baseline escalation. | `T3-MX-01` exact lookup and rationale. |
| `MX-LM` | low | moderate | P3 | Limited reach but recurring cost requires normal-window attention. | One user's OneDrive intermittently pauses; local copy permits work but creates rework. | Confirm recurrence and workaround burden; otherwise low urgency may apply. | N1; no baseline escalation. | `T3-MX-02` exact lookup and evidence requirement. |
| `MX-LH` | low | high | P2 | Small scope with near-term material time pressure. | One presenter cannot access a shared mailbox needed for a meeting within hours; delegated backup exists but is fragile. | A stated deadline without consequence/time owner is not enough; collect deadline evidence. | N1 expedited; conditional escalation. | `T3-MX-03` P2 floor for high urgency and conditional route. |
| `MX-LC` | low | critical | P2 | Immediate action is needed despite limited business consequence; P1 is reserved for both dimensions critical. | One technician cannot access a short-lived, non-critical lab slot occurring now; no alternate user is available and wider operations are unaffected. | Critical urgency with low impact is exceptional: confirm the immediate window and limited consequence. Security/safety/data-integrity signals require reassessing impact. | N2; mandatory escalation. | `T3-MX-04` P2 result, N2, escalation and exceptional-boundary evidence. |
| `MX-ML` | moderate | low | P3 | Team-level or important-function impact is stable and schedulable. | Several users have a non-critical SharePoint navigation defect with a reliable direct-link workaround. | If affected scope is unverified, ask for population/source; if the workaround is fragile, reassess urgency. | N1; no baseline escalation. | `T3-MX-05` exact lookup and scope evidence. |
| `MX-MM` | moderate | moderate | P3 | Moderate reach and accumulating operational burden without imminent severe harm. | A team has intermittent network drops; work continues but calls reconnect several times daily. | Increased frequency, failed workaround, or current-shift deadline can raise urgency. | N1; conditional escalation after N1 limits. | `T3-MX-06` exact lookup and N1-limit escalation. |
| `MX-MH` | moderate | high | P2 | Affected team/function faces significant disruption within hours. | Finance users cannot synchronize files needed for the current-day close; manual transfer is capacity-limited. | Confirm the deadline, affected function and workaround capacity. | N2 recommended; conditional escalation. | `T3-MX-07` exact lookup, N2 recommendation and gaps. |
| `MX-MC` | moderate | critical | P2 | Immediate harm warrants P2, but impact is not yet critical. | A small team has no access to the only operational SharePoint folder during an active cutover. | Reassess impact if the cutover is mission-critical or exposure spreads. | N2; mandatory escalation. | `T3-MX-08` P2 result, mandatory escalation and impact reassessment. |
| `MX-HL` | high | low | P2 | Broad/material impact requires elevated coordination even while stable. | A department-wide non-critical application feature is unavailable; a reliable workaround supports planned processing. | Verify breadth and workaround effectiveness; isolated inconvenience must not be labeled high. | N2; mandatory escalation. | `T3-MX-09` P2 floor for high impact and N2 escalation. |
| `MX-HM` | high | moderate | P2 | Significant scope plus accumulating degradation needs prioritized recovery. | Multiple sites have slow access to a shared service; core work continues with material delay. | Confirm sites/users and trend; widespread cosmetic impact may be moderate instead. | N2; mandatory escalation. | `T3-MX-10` exact lookup and high-impact escalation. |
| `MX-HH` | high | high | P2 | Serious scope and near-term harm, short of simultaneous critical impact and urgency. | A department cannot reach the network before a current-shift processing deadline; a limited fallback serves only some users. | If enterprise scope, active material loss, or no containment is confirmed, reassess as critical. | N2; mandatory escalation. | `T3-MX-11` high/high remains P2 and checks P1 boundary. |
| `MX-HC` | high | critical | P2 | Harm is immediate and scope is high, but P1 requires critical impact too. | Multiple teams are locked out of Entra ID during active operations, with no viable workaround; enterprise scope is not confirmed. | Immediately ask whether mission-critical/enterprise effects make impact critical. | N2; mandatory escalation and troubleshooting stop until coordinated. | `T3-MX-12` P2/P1 boundary, blocking question and stop. |
| `MX-CL` | critical | low | P2 | Critical consequence/scope is supported, but condition is contained and safely schedulable. | A widespread data-integrity defect is fully contained; validated recovery is scheduled and no further writes occur. | Critical+low is exceptional: containment, stability and acceptable delay all require corroboration; otherwise raise urgency. | N2; mandatory escalation. | `T3-MX-13` exceptional boundary requires containment evidence. |
| `MX-CM` | critical | moderate | P2 | Critical impact is contained enough to avoid immediate response, but coordinated recovery remains elevated. | Enterprise file access is impaired; a tested read-only continuity process works through the next business window. | If continuity cannot support the window or harm resumes, urgency becomes high/critical. | N2; mandatory escalation. | `T3-MX-14` exact lookup and continuity evidence. |
| `MX-CH` | critical | high | P2 | Critical scope/consequence with near-term, not yet immediate, escalation of harm. | A core enterprise service is degraded before a processing cutoff within hours; workaround capacity is temporary. | Immediate active loss or exhausted workaround raises urgency to critical and therefore P1. | N2; mandatory escalation and continuous reassessment. | `T3-MX-15` P2/P1 time boundary and reassessment flag. |
| `MX-CC` | critical | critical | P1 | Critical business consequence and immediate/rapidly increasing harm coincide. | Enterprise authentication outage stops mission-critical work with no viable workaround. | Both dimensions require evidence; if either is unsupported, classification remains incomplete rather than silently downgraded. | N2/incident coordination; immediate mandatory escalation and stop uncoordinated changes. | `T3-MX-16` sole P1 cell, blocking escalation and evidence validation. |

Compact lookup view:

| Impact \ Urgency | low | moderate | high | critical |
|---|---:|---:|---:|---:|
| low | P4 | P3 | P2 | P2 |
| moderate | P3 | P3 | P2 | P2 |
| high | P2 | P2 | P2 | P2 |
| critical | P2 | P2 | P2 | P1 |

## Escalation rules

Evaluation is deterministic and additive. Routes form the strict total order
`N1 < N2 < incident_coordination`; the highest applicable route wins. Each
`ESC-*` rule declares its destination, every matching reason is retained, and a
lower-ranked rule never replaces a higher-ranked route. Escalation never lowers
priority.

### Mandatory escalation to N2 / incident coordination

Record `escalation_required=true`, every matched reason ID, and the winning route
when any condition is true:

- `ESC-01` -> `incident_coordination`: priority is P1.
- `ESC-02` -> `N2`: impact is high or critical, or urgency is critical. When
  `ESC-01` also matches, `incident_coordination` wins by route rank.
- `ESC-03` -> `incident_coordination`: structured risk assessment is `suspected`
  or `confirmed` with at least one closed-catalog risk-signal ID.
- `ESC-04` -> `N2`: resolution or diagnostic access requires administrative
  privilege, production configuration change, server/cloud tenant change, or an
  action outside the approved N1 boundary.
- `ESC-05` -> `incident_coordination`: incident spans multiple teams/sites/services
  or requires ownership by another resolver group/vendor.
- `ESC-06` -> `N2`: supported N1 checks are exhausted, evidence conflicts, the
  cause remains materially uncertain, or the incident recurs after a documented
  prior fix.

Planned tests: `T3-ESC-01` through `T3-ESC-06` prove each destination,
`T3-ESC-07` proves simultaneous reasons are retained, `T3-ESC-08` proves
escalation cannot reduce priority, and `T3-ESC-13` proves route ordering and the
highest-route rule.

### Conditional escalation

For `MX-LH`, `MX-MM`, and `MX-MH`, begin with the baseline owner only if required
evidence is complete and no mandatory trigger applies. `MX-LH` and `MX-MM` route
from baseline N1 to N2 when a conditional trigger matches. `MX-MH`, whose baseline
is already N2, routes to `incident_coordination` when a conditional trigger
matches. Conditional triggers are:

- the documented baseline-owner verification limit is reached without the
  expected result;
- the workaround fails or scope/time-to-harm increases;
- required logs or settings are inaccessible to the baseline owner;
- the runbook is absent, ambiguous, contradictory, or outside its supported scope.

Planned tests: `T3-ESC-09` through `T3-ESC-12`, including the distinct N1-to-N2
and N2-to-incident-coordination outcomes.
## N1 and N2 recommendation policy

### Recommend N1

All of the following must be true:

1. Matrix baseline is N1 and no escalation trigger applies.
2. Scope, time-to-harm, symptoms, errors, and prior actions are sufficiently known.
3. The scenario is within an approved runbook or a non-invasive evidence-collection
   procedure.
4. No administrative privilege, configuration mutation, destructive operation,
   tenant/server access, security containment, or cross-team coordination is needed.
5. The expected result and stopping condition are explicit.

N1 may always perform safe intake, evidence preservation, duplicate detection, and
known-service-status checks while escalation is being arranged.

### Recommend N2

Recommend N2 when the matrix says N2 or any `ESC-*` condition applies. N2 remains
advisory ownership in this local product: it neither grants privileges nor proves
authorization. Any potentially destructive, administrative, or configuration
changing action still requires a separate human-approval record and is never
executed by SupportOps.

Planned tests: `T3-LVL-01` N1 all-conditions path; `T3-LVL-02` each prohibited N1
condition routes N2; `T3-LVL-03` N1 intake remains allowed during escalation;
`T3-LVL-04` recommendation does not create approval or execution capability.

## Evidence collection and diagnostic questions

Questions are generated from absent or contradictory structured facts. Already
answered questions are not repeated. A blocking question is displayed before any
solution or plan; optional questions may accompany the triage result.

Risk assessment is structured and never inferred from title, description, symptoms,
errors, or other free text. It has:

- `risk_assessment_status`: exactly one of `not_assessed`, `none_identified`,
  `suspected`, or `confirmed`;
- `risk_signal_ids`: a unique subset of the closed catalog
  `security_compromise`, `credential_exposure`, `safety_hazard`,
  `privacy_exposure`, `regulatory_exposure`, `data_integrity_loss`.

`not_assessed` and `none_identified` require an empty ID list. `suspected` and
`confirmed` require at least one catalog ID. Unknown IDs or inconsistent pairs are
rejected safely. `not_assessed` generates blocking `DQ-10`; `none_identified` does
not repeat it; `suspected` or `confirmed` triggers `ESC-03` and `STOP-01` without
re-asking the answered question. Free text alone can never set a risk status or ID.
Planned tests: `T3-RISK-01..06` cover the four statuses, unknown IDs, inconsistent
pairs, no free-text inference, escalation and stop effects.
| ID | Proposed question | Evidence captured | Blocking condition | Planned test |
|---|---|---|---|---|
| `DQ-01` | Quantas pessoas, dispositivos, equipes e localidades estão afetados? Como essa estimativa foi obtida? | Population, scope, source. | Impact is absent, high/critical without scope support, or reports conflict. | `T3-DQ-01` |
| `DQ-02` | Qual serviço, função e processo de negócio estão afetados? O processo é crítico? | Service/function/process criticality. | Affected service/process is absent or criticality claim is unsupported. | `T3-DQ-02` |
| `DQ-03` | Existe contorno? Ele foi testado, preserva a tarefa essencial e por quanto tempo suporta a operação? | Workaround availability, validation and capacity. | Urgency is high/critical, or impact depends on workaround viability. | `T3-DQ-03` |
| `DQ-04` | Qual é o prazo ou janela operacional relevante, quem o confirmou e qual é a consequência concreta do atraso? | Deadline, owner, consequence, time-to-harm. | Urgency is high/critical or requester only supplied an urgency label. | `T3-DQ-04` |
| `DQ-05` | Quando começou, a falha é contínua ou intermitente e está estável, melhorando ou piorando? | Timeline, frequency and trend. | Time-to-harm or recurrence is unknown. | `T3-DQ-05` |
| `DQ-06` | Quais sintomas e mensagens de erro exatas foram observados, em que horário e em qual sistema? | Timestamped symptoms/errors/system. | Symptom/error context is absent or inconsistent. | `T3-DQ-06` |
| `DQ-07` | Quais ações já foram realizadas, por quem, em que ordem e com qual resultado? | Prior-action audit and outcomes. | Prior actions are unknown, risky, or may have changed state. | `T3-DQ-07` |
| `DQ-08` | Houve mudança recente de conta, permissão, dispositivo, rede, aplicação ou configuração? | Change correlation. | Failure followed a change or cause remains unclear. | `T3-DQ-08` |
| `DQ-09` | Há alerta oficial, incidente correlato ou outros chamados do mesmo serviço? | Corroboration and possible major-incident scope. | High/critical impact or multi-user suspicion lacks corroboration. | `T3-DQ-09` |
| `DQ-10` | Selecione o estado da avaliação de risco e, para suspeita ou confirmação, os IDs aplicáveis do catálogo fechado. | Structured risk status and closed-catalog IDs. | `risk_assessment_status` is absent or `not_assessed`; never triggered by free-text inference. | `T3-DQ-10`, `T3-RISK-01..06` |
| `DQ-11` | A coleta exige privilégio administrativo, alteração de configuração ou acesso fora da responsabilidade do N1? | Privilege/change/ownership boundary. | Next verification crosses N1 or safe-read-only boundary. | `T3-DQ-11` |
| `DQ-12` | O problema pode ser reproduzido com segurança? Em caso afirmativo, quais são os passos e o resultado esperado? | Safe reproducibility and expected behavior. | A controlled test is being considered without safe reproduction criteria. | `T3-DQ-12` |

Additional evidence is mandatory when either classification dimension is missing,
has no supporting facts, conflicts with another answer, uses an unknown enum, or
would change by two or more priority levels depending on the unanswered fact.
The output is then `triage_incomplete`; no priority, support level, or solution is
fabricated. Planned tests: `T3-GAP-01` through `T3-GAP-06`, including no duplicate
questions and blocking questions preceding solution content.

## Troubleshooting interruption criteria

SupportOps must return a structured `stop` outcome, preserve evidence, display the
reason, and recommend the responsible escalation path when any rule matches:

- `STOP-01`: structured `risk_assessment_status` is `suspected` or `confirmed`
  with at least one valid closed-catalog risk-signal ID. Free text never triggers
  or clears this stop rule.
- `STOP-02`: a next step would be destructive, administrative, configuration
  changing, outside the approved runbook, or lacks required human approval.
- `STOP-03`: scope or urgency is increasing during diagnosis, especially a possible
  transition to P1.
- `STOP-04`: evidence is contradictory or insufficient for the next safe step.
- `STOP-05`: two controlled attempts produce unexpected results, or a retry risks
  compounding impact; repeated attempts are not proposed.
- `STOP-06`: system ownership, authorization, maintenance window, backup/rollback,
  or recovery criteria are unknown where the next action depends on them.
- `STOP-07`: a vendor/resolver-group boundary is reached or a known major incident
  procedure supersedes local troubleshooting.

Stopping does not close the incident, approve an action, or execute anything.
Planned tests: `T3-STOP-01` through `T3-STOP-07`, `T3-STOP-08` stop precedes plan,
and `T3-STOP-09` stop has no lifecycle/approval/execution side effect.

## Configuration, versioning, and fail-closed behavior

The implementation story must provide one application-owned, reviewable policy
artifact inside the project. Its schema must require:

- policy/schema/matrix versions and an effective date;
- exactly the four allowed impact values, four urgency values and priorities P1-P4;
- exactly one rule for every Cartesian combination and stable unique rule IDs;
- rationale and baseline routing for every rule;
- explicit escalation, evidence-gap, and stop-rule collections;
- a declared `fallback_behavior: fail_closed` value;
- a checksum or equivalent immutable revision reference stored with results.

Startup must fail with a safe actionable configuration error naming the invalid
project-relative configuration identifier, not its contents or sensitive incident
data. Missing cells, duplicates, unknown values, invalid versions, contradictory
P1 mapping, unavailable/unreadable configuration, or unsupported schema versions
are fatal. Reload during a running operation is not part of ST-03.

Planned tests: `T3-CFG-01` valid load; `T3-CFG-02` all 16 unique combinations;
`T3-CFG-03` missing rule; `T3-CFG-04` duplicate; `T3-CFG-05` unknown enum;
`T3-CFG-06` malformed/unreadable; `T3-CFG-07` unsupported version;
`T3-CFG-08` P1 boundary invariant; `T3-CFG-09` safe error/redaction;
`T3-CFG-10` no fallback; `T3-CFG-11` result retains exact policy revision.

## Planned scenario and contract tests

In addition to the per-rule IDs above:

- `T3-IMP-01..04`: each impact level accepts its minimum evidence.
- `T3-IMP-05`: highest supported impact wins; requester role alone does not.
- `T3-URG-01..04`: each urgency level accepts its minimum evidence.
- `T3-URG-05`: requester wording alone does not raise urgency.
- `T3-PRI-01`: all 16 cells match the compact matrix.
- `T3-PRI-02`: P1 exists only for critical/critical.
- `T3-PRI-03`: high or critical dimension never produces P3/P4.
- `T3-PRI-04`: priority calculation is deterministic and repeatable offline.
- `T3-CLI-01`: CLI classifies a persisted non-deleted incident and emits a stable
  human-readable result.
- `T3-CLI-02`: machine-readable CLI output includes rule and version traceability.
- `T3-CLI-03`: CLI displays blocking questions before any troubleshooting content.
- `T3-CLI-04`: deleted/unknown incident cannot be operationally triaged.
- `T3-INT-01`: persisted triage snapshot round-trips with exact policy revision.
- `T3-INT-02`: re-triage creates a new immutable snapshot rather than overwriting.
- `T3-SEC-01`: no shell/subprocess/executor API exists.
- `T3-SEC-02`: hostile text remains data and cannot alter the selected rule.
- `T3-SEC-03`: errors/logs omit incident descriptions, tokens and configuration
  contents.
- `T3-REG-01`: all ST-01 and ST-02 tests remain green.

## Explicit non-goals for this policy preparation

- No code, database migration, CLI command, Streamlit screen, runbook, hypothesis
  engine, troubleshooting executor, shell/subprocess capability, or LLM provider.
- No automatic priority override based on category or identity.
- No remote Git configuration, push, or file outside the isolated project.
- No claim that any planned test currently passes.
