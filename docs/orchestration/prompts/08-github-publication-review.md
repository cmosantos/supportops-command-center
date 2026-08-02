# GitHub Publication Review Prompt

```text
Prepare this repository for professional public review, but do not create a remote or push.

Inspect every tracked file for:
- credentials, tokens, private keys, personal paths, usernames, email addresses, client/company names, real incident data, logs, databases, exports, caches, and environment files;
- inaccurate claims, stale counts, broken links, and undocumented limitations;
- missing README sections, screenshots, architecture, installation, demo, testing, security, contributing, changelog, release notes, issue templates, and CI;
- publication risks in prompts/orchestration artifacts.

Requirements:
- English public documentation;
- synthetic screenshots only;
- clear runtime vs. AI-assisted development distinction;
- honest limitations and security boundaries;
- no license selection without human approval;
- no remote, push, tag, release, deployment, registry, or package publication.

Return:
- publication PASS/FAIL;
- files changed;
- secret/PII/path scan evidence;
- suggested repository description and topics;
- remaining human checklist.
```
