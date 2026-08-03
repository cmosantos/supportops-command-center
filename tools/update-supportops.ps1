param(
    [string]$ProjectPath = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $Command $($Arguments -join ' ')"
    }
}

function Resolve-ProjectPath {
    param([string]$RequestedPath)

    $candidates = @(
        $RequestedPath,
        (Join-Path $RequestedPath "supportops-command-center"),
        (Join-Path $HOME "supportops-command-center"),
        (Join-Path $HOME "Desktop\supportops-command-center"),
        (Join-Path $HOME "Documents\supportops-command-center"),
        (Join-Path $HOME "Downloads\supportops-command-center"),
        (Join-Path $HOME "source\repos\supportops-command-center"),
        (Join-Path $HOME "OneDrive\supportops-command-center"),
        (Join-Path $HOME "OneDrive\Desktop\supportops-command-center"),
        (Join-Path $HOME "OneDrive\Documents\supportops-command-center")
    ) | Select-Object -Unique

    foreach ($candidate in $candidates) {
        if ((Test-Path -LiteralPath $candidate -PathType Container) -and
            (Test-Path -LiteralPath (Join-Path $candidate ".git") -PathType Container)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    throw "SupportOps repository not found. Open CMD inside the supportops-command-center folder and run the command again."
}

try {
    $Host.UI.RawUI.WindowTitle = "SupportOps - Full update"

    Write-Host "SupportOps Command Center - automatic update" -ForegroundColor Green
    Write-Host "This process preserves local changes in a Git stash before updating." -ForegroundColor DarkGray

    foreach ($requiredCommand in @("git", "docker")) {
        if (-not (Get-Command $requiredCommand -ErrorAction SilentlyContinue)) {
            throw "$requiredCommand was not found in PATH."
        }
    }

    Write-Step "Locating the project"
    $resolvedProjectPath = Resolve-ProjectPath -RequestedPath $ProjectPath
    Set-Location -LiteralPath $resolvedProjectPath
    Write-Host "Project: $resolvedProjectPath"

    Write-Step "Checking Docker Desktop"
    Invoke-Native docker info
    Invoke-Native docker compose version

    Write-Step "Protecting local changes"
    $workingTreeChanges = & git status --porcelain
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to read the Git working tree."
    }

    if ($workingTreeChanges) {
        $backupName = "SupportOps automatic backup $(Get-Date -Format 'yyyy-MM-dd HH-mm-ss')"
        Invoke-Native git stash push --include-untracked -m $backupName
        Write-Host "Local changes saved in Git stash: $backupName" -ForegroundColor Yellow
    }
    else {
        Write-Host "No local changes to back up."
    }

    Write-Step "Synchronizing the exact GitHub main branch"
    Invoke-Native git fetch --prune origin main
    Invoke-Native git switch main
    Invoke-Native git reset --hard origin/main
    Invoke-Native git clean -fd

    $commit = (& git rev-parse --short HEAD).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to read the current commit."
    }
    Write-Host "Updated commit: $commit" -ForegroundColor Green

    Write-Step "Removing the old SupportOps container and image"
    & docker compose down --remove-orphans
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to stop the existing SupportOps container."
    }

    & docker image rm supportops-command-center:1.0.0-local 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Old image removed."
    }
    else {
        Write-Host "No removable old image was found; continuing."
    }

    Write-Step "Building SupportOps from scratch (no Docker cache)"
    Invoke-Native docker compose build --pull --no-cache app

    Write-Step "Starting a fresh SupportOps container"
    Invoke-Native docker compose up -d --force-recreate app

    Write-Step "Waiting for the application health check"
    $healthUrl = "http://127.0.0.1:8501/_stcore/health"
    $ready = $false
    for ($attempt = 1; $attempt -le 45; $attempt++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                $ready = $true
                break
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
    }

    if (-not $ready) {
        & docker compose ps
        & docker compose logs --tail 80 app
        throw "SupportOps did not become healthy. The latest container logs are shown above."
    }

    Write-Step "Update completed"
    & docker compose ps
    Write-Host "SupportOps is running from commit $commit." -ForegroundColor Green
    Write-Host "The production interface is fixed to English." -ForegroundColor Green

    $appUrl = "http://127.0.0.1:8501/?updated=$commit"
    Start-Process $appUrl
    Write-Host "Opened: $appUrl"
}
catch {
    Write-Host "`nUPDATE FAILED" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "`nNothing was silently discarded. Any detected local changes were saved in Git stash." -ForegroundColor Yellow
    exit 1
}
finally {
    Write-Host ""
    Read-Host "Press Enter to close"
}
