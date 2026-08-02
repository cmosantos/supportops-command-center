# Orchestration Playbook

## Objective

Turn a broad product request into a traceable engineering campaign with bounded scope, explicit authority, independent review, and reproducible evidence.

## Roles

| Role | Primary responsibility | Must not self-approve |
|---|---|---|
| Product/Analyst | Problem, personas, requirements, acceptance criteria, exclusions | Architecture or implementation completion |
| Architect | Boundaries, dependencies, ADRs, threat model, increment plan | Functional completion |
| Developer | Implement approved stories and focused tests | Final QA acceptance |
| QA | Validate criteria, regression, negative paths, and usability | Implement undocumented scope expansion |
| Security/Critic | Challenge trust boundaries, data handling, unsafe capabilities | Waive Critical/High findings silently |
| DevOps/Delivery | Build, package, container, CI, repository hygiene, release readiness | External publication without approval |
| Orchestrator | Sequence roles, enforce gates, maintain checkpoints | Override human-controlled decisions |
| Human owner | Scope, risk acceptance, architecture approval, external actions | Delegate accountability entirely to automation |

## Operating principles

1. **Repository evidence is the source of truth.** Read code, stories, ADRs, tests, and Git state before acting.
2. **One bounded increment at a time.** Every increment has acceptance criteria, tests, evidence, and a checkpoint.
3. **Independent review.** The implementation role does not declare itself fully accepted.
4. **Fail closed.** Ambiguous requirements, destructive actions, credentials, remote publication, and unresolved Critical/High findings require human input.
5. **No hidden scope expansion.** Improvements outside approved criteria become backlog items.
6. **Safe autonomy.** Local, reversible, project-contained actions may proceed; external or destructive actions remain human-controlled.
7. **Evidence over confidence.** “Done” requires commands, outputs, counts, files, and Git status—not persuasive language.

## Standard gate

An increment can close only when all applicable checks are complete:

- acceptance criteria mapped to evidence;
- focused tests added and passing;
- full regression passing;
- static analysis/type checking passing;
- security boundaries revalidated;
- build/package/install smoke passing where applicable;
- documentation and exact file list updated;
- independent QA review complete;
- local commit created;
- worktree clean;
- remote/push/tag/release state explicitly reported.

## Autonomy boundary

The campaign may normally perform:

- project-local file creation and edits;
- project-local dependency synchronization;
- tests, linters, type checking, builds, package inspection, and container validation;
- local Git commits;
- documentation, diagrams, synthetic examples, and publication preparation.

The campaign must stop for:

- changes outside `<PROJECT_ROOT>`;
- deletion of persistent data or broad directories;
- credentials, tokens, private keys, or real customer data;
- global machine configuration or unapproved global installs;
- material architecture/scope changes;
- unresolved Critical/High findings;
- license selection;
- remote creation, GitHub configuration, push, tag, release, deployment, registry, or external communication.

## Checkpoint contract

Every pause or completion report should include:

- current version and branch;
- completed and pending stories;
- acceptance-criteria status;
- test and quality results;
- known findings by severity;
- latest commits;
- `git status` and remote state;
- exact resume instruction;
- decisions still owned by a human.
