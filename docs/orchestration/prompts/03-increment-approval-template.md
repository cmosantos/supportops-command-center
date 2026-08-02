# Increment Approval Template

```text
Authorize only this increment:
<STORY_ID_AND_TITLE>

Approved scope:
<APPROVED_SCOPE>

Required acceptance criteria:
<CRITERIA>

Required evidence:
- focused tests;
- full regression;
- static analysis/type checking;
- security checks for affected boundaries;
- documentation and exact file list;
- independent QA review;
- one local commit and clean worktree.

Constraints:
- no scope expansion;
- no actions outside <PROJECT_ROOT>;
- no credentials, real data, remote, push, tag, release, deployment, or license choice;
- stop for material architecture changes or unresolved Critical/High findings.

After completion, report results and wait for the next authorization.
```
