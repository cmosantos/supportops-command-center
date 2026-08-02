# Screenshot Acquisition Guide

The repository includes a small set of sanitized visuals under `docs/assets/`. They were captured from a local Docker-backed application using synthetic data only.

## Recommended gallery

Capture these views when refreshing publication assets:

1. database health and dashboard;
2. incident list and detail;
3. deterministic triage result/questions;
4. runbook ranking and evidence;
5. performed procedure and nine-section document;
6. export result.

Use descriptive names under `docs/assets/`, for example:

```text
dashboard-overview.png
incident-lifecycle.png
triage-result.png
runbook-search.png
procedures-and-documentation.png
export-result.png
```

## Safe capture process

Use only the synthetic demo database prepared with `scripts/prepare_screenshot_demo.ps1` or equivalent synthetic data.

Before capture, verify that the browser, taskbar, terminal, and application contain no:

- real names or incident data;
- personal or developer paths;
- usernames, hostnames, email addresses, or notifications;
- tokens, credentials, private keys, or internal URLs;
- client or employer identifiers.

Crop to the application surface, review the image at full resolution, and perform a second manual review before committing it. The current UI is Portuguese-first; English localization is a roadmap item.
