# Complete Synthetic Demonstration

Run from the project root in PowerShell. All values are synthetic; the temporary
database and exports remain in ignored project-owned directories.

```powershell
$env:SUPPORTOPS_DB_PATH = "data/demo-v1.db"
$env:SUPPORTOPS_EXPORT_ROOT = "exports/demo-v1"
uv run supportops config validate
uv run supportops db status
uv run supportops db init

$incident = (uv run supportops incident create --title "Synthetic OneDrive sync" --description "Training record; client paused" --affected-party "Example User" --affected-service "OneDrive" --impact moderate --urgency moderate --symptoms "No synchronization" --category storage --actor demo-analyst | ConvertFrom-Json).id
uv run supportops incident get $incident
uv run supportops incident update $incident --expected-version 1 --symptoms "Synthetic client remains paused" --actor demo-analyst
uv run supportops incident close $incident --actor demo-analyst
uv run supportops incident reopen $incident --actor demo-analyst
uv run supportops incident history $incident

# Deliberately incomplete evidence demonstrates deterministic diagnostic questions.
uv run supportops triage run $incident --evidence-json '{"impact":"moderate","urgency":"moderate"}' --actor demo-analyst --format json
uv run supportops triage history $incident --format json
uv run supportops knowledge search "onedrive sincronização" --limit 3 --format json

uv run supportops performed record $incident --description "Checked client state" --result "Client was paused" --actor demo-analyst --format json
uv run supportops performed list $incident --format json
uv run supportops document generate $incident --actor demo-analyst --format json
uv run supportops document show $incident --revision 1 --format json
uv run supportops document history $incident --format json
uv run supportops export $incident --revision 1 --format markdown --output json
uv run supportops export $incident --revision 1 --format json --output json
```

Start the same UI over the persisted demo and inspect incident history, triage,
runbook evidence, documentation and dashboard:

```powershell
uv run streamlit run src/supportops/streamlit_app.py --server.address=127.0.0.1
```

No step executes a suggested command, accesses Microsoft 365, calls a ticket API,
uses credentials, or contacts an LLM. Review both export files as sensitive
operational records even though this demonstration uses synthetic data. Follow
the safe-reset guidance instead of deleting broad directories or Docker volumes.
