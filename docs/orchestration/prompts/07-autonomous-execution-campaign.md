# Controlled Autonomous Execution Campaign

```text
Execute the following approved increments sequentially:
<INCREMENT_LIST>

Autonomy is authorized only for safe, reversible, project-local actions inside <PROJECT_ROOT>, including code/docs/tests, local dependencies, builds, package inspection, Docker validation, and local commits.

For each increment:
1. Confirm story and acceptance criteria.
2. Implement the smallest complete slice.
3. Add focused tests and run full regression.
4. Run independent QA/security/delivery review.
5. Correct findings and rerun affected gates.
6. Update story, evidence, documentation, and file list.
7. Commit locally and verify a clean worktree.
8. Proceed only when the increment gate passes.

Ask the human only for:
- actions outside <PROJECT_ROOT>;
- destructive persistent-data operations;
- credentials or real data;
- global machine changes;
- material scope/architecture changes;
- unresolved Critical/High findings;
- license selection;
- remote, push, tag, release, deploy, registry, or external communication.

At campaign end, provide one consolidated report covering version, stories, criteria, functionality, commands, Docker, commits, tests, findings, Git state, publication readiness, and remaining human decisions. Do not begin optional roadmap work.
```
