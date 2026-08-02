# Screenshot Acquisition Guide

Screenshots are intentionally not committed by ST-08. Create them only from the
synthetic demo database using `scripts/prepare_screenshot_demo.ps1`.

Capture: database health; incident list/detail; triage result/questions; knowledge
ranking/evidence; performed procedure and nine-section document; export result;
dashboard. Use names `01-health.png` through `07-dashboard.png` under ignored
`screenshots/`.

Before capture, verify that the browser, taskbar, terminal and UI contain no real
names, incident IDs, paths, hosts, usernames, email addresses, tokens or other
notifications. Crop only the application surface. Perform a second manual review
before publication. Stop the local server and remove only the exact generated
temporary database/export/screenshot targets when evidence retention is unnecessary.
