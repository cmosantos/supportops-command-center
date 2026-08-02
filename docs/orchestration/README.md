# AI Engineering Orchestration

This directory documents the engineering method used to build SupportOps Command Center.

The project used a role-gated workflow for product discovery, architecture, development, QA, security, and delivery. The orchestration framework defined responsibilities and gates; the coding model used the CLI to inspect the repository, edit files, run tests, build packages, validate Docker, and create local commits. Human approval controlled scope, architecture, sensitive actions, and publication.

These files are:

- sanitized for public use;
- reusable across projects;
- independent of personal paths, organizations, clients, credentials, and local machine details;
- **not verbatim conversation transcripts**;
- **not runtime dependencies** of SupportOps.

## Contents

- [`ORCHESTRATION_PLAYBOOK.md`](ORCHESTRATION_PLAYBOOK.md) — roles, gates, evidence, and operating model.
- [`prompts/01-project-bootstrap.md`](prompts/01-project-bootstrap.md) — start an isolated project.
- [`prompts/02-architecture-review.md`](prompts/02-architecture-review.md) — architecture and boundary review.
- [`prompts/03-increment-approval-template.md`](prompts/03-increment-approval-template.md) — authorize one bounded increment.
- [`prompts/04-quality-verification.md`](prompts/04-quality-verification.md) — run independent quality and security checks.
- [`prompts/05-checkpoint-and-pause.md`](prompts/05-checkpoint-and-pause.md) — stop safely with a resumable checkpoint.
- [`prompts/06-project-resume.md`](prompts/06-project-resume.md) — resume from repository evidence.
- [`prompts/07-autonomous-execution-campaign.md`](prompts/07-autonomous-execution-campaign.md) — execute a controlled multi-increment campaign.
- [`prompts/08-github-publication-review.md`](prompts/08-github-publication-review.md) — prepare publication without creating a remote or pushing.

## Transparency note

A named “agent” in this workflow represents a role, instruction set, authority boundary, and review perspective. It does not necessarily mean a permanently independent process. The same coding model may execute different roles under separate rules and gates.
