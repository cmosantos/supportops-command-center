param(
    [string]$RuntimeRoot = ".screenshot-demo"
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\$RuntimeRoot"))
$project = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$relative = [System.IO.Path]::GetRelativePath($project, $root)
if (
    [System.IO.Path]::IsPathRooted($relative) -or
    $relative -eq ".." -or
    $relative.StartsWith(".." + [System.IO.Path]::DirectorySeparatorChar)
) {
    throw "Runtime root must remain inside the project."
}
$current = $project
foreach ($segment in ($relative -split '[\\/]')) {
    if (-not $segment) { continue }
    $current = Join-Path $current $segment
    if (Test-Path -LiteralPath $current) {
        $item = Get-Item -Force -LiteralPath $current
        if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            throw "Runtime root must not contain a reparse point."
        }
    }
}
$env:SUPPORTOPS_DB_PATH = Join-Path $root "data\supportops.db"
$env:SUPPORTOPS_EXPORT_ROOT = Join-Path $root "exports"
$env:SUPPORTOPS_LLM_ENABLED = "false"
New-Item -ItemType Directory -Force -Path $root | Out-Null
uv run supportops db init
uv run supportops incident create --title "Synthetic OneDrive sync" --description "Training record; client paused" --affected-party "Example User" --affected-service "OneDrive" --impact moderate --urgency moderate --symptoms "No synchronization" --category storage --actor demo-analyst
Write-Host "Synthetic database ready at the ignored project-local runtime root."
Write-Host "Start Streamlit manually and follow docs/guides/screenshots.md."
