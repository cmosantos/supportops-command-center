# Project Bootstrap Prompt

Use this template to begin a new isolated project.

```text
Act as the project orchestrator.

Create and operate only inside:
<PROJECT_ROOT>

Goal:
<PRODUCT_GOAL>

Before implementation:
1. Inspect the current repository and confirm isolation.
2. Document problem, users, workflows, requirements, non-goals, risks, and success criteria.
3. Propose a modular architecture, security boundaries, stories, acceptance criteria, test strategy, and incremental delivery plan.
4. Identify decisions that require human approval.
5. Initialize local Git only if explicitly allowed.

Do not:
- modify framework/core files outside <PROJECT_ROOT>;
- use credentials or real customer data;
- create a remote, push, deploy, tag, release, or select a license;
- implement beyond the approved phase.

Deliver a reviewable discovery/architecture checkpoint and stop for approval.
```
