# Checkpoint and Pause Prompt

```text
Stop new implementation after the current safe operation.

Create a resumable checkpoint containing:
- current version, branch, and worktree state;
- completed/pending stories and acceptance criteria;
- test, quality, security, build, and container results;
- known findings and risks;
- changed files and latest commits;
- remote/tag/release state;
- exact next command or prompt needed to resume.

Commit only approved project-local work if gates pass.
Do not start another increment, create a remote, push, tag, release, deploy, or delete persistent data.
```
