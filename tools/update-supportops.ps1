param(
    [string]$ProjectPath = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$RepositoryUrl = "https://github.com/cmosantos/supportops-command-center.git"

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

function Test-SupportOpsRepository {
    param([string]$Candidate)

    return (
        (Test-Path -LiteralPath $Candidate -PathType Container) -and
        (Test-Path -LiteralPath (Join-Path $Candidate ".git") -PathType Container) -and
        (Test-Path -LiteralPath (Join-Path $Candidate "compose.yaml") -PathType Leaf)
    )
}

function Resolve-Or-CloneProject {
    param([string]$RequestedPath)

    $candidates = @(
        $RequestedPath,
        (Join-Path $RequestedPath "supportops-command-center"),
        (Join-Path $HOME "supportops-command-center"),
        (Join-Path $HOME "SupportOps\supportops-command-center"),
        (Join-Path $HOME "Desktop\supportops-command-center"),
        (Join-Path $HOME "Documents\supportops-command-center"),
        (Join-Path $HOME "Downloads\supportops-command-center"),
        (Join-Path $HOME "source\repos\supportops-command-center"),
        (Join-Path $HOME "OneDrive\supportops-command-center"),
        (Join-Path $HOME "OneDrive\Desktop\supportops-command-center"),
        (Join-Path $HOME "OneDrive\Documents\supportops-command-center")
    ) | Select-Object -Unique

    foreach ($candidate in $candidates) {
        if (Test-SupportOpsRepository -Candidate $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    Write-Host "No local SupportOps repository was found." -ForegroundColor Yellow
    Write-Host "A clean copy will be downloaded automatically." -ForegroundColor Yellow

    $managedRoot = Join-Path $HOME "SupportOps"
    New-Item -ItemType Directory -Path $managedRoot -Force | Out-Null
    $cloneTarget = Join-Path $managedRoot "supportops-command-center"

    if (Test-Path -LiteralPath $cloneTarget) {
        if (Test-SupportOpsRepository -Candidate $cloneTarget) {
            return (Resolve-Path -LiteralPath $cloneTarget).Path
        }

        $cloneTarget = Join-Path $managedRoot (
            "supportops-command-center-" + (Get-Date -Format "yyyyMMdd-HHmmss")
        )
    }

    Write-Step "Downloading a clean SupportOps repository"
    Invoke-Native git clone $RepositoryUrl $cloneTarget

    if (-not (Test-SupportOpsRepository -Candidate $cloneTarget)) {
        throw "The clean SupportOps repository could not be prepared."
    }

    return (Resolve-Path -LiteralPath $cloneTarget).Path
}

try {
    $Host.UI.RawUI.WindowTitle = "SupportOps - Full update"

    Write-Host "SupportOps Command Center - automatic update" -ForegroundColor Green
    Write-Host "This process preserves local changes before updating." -ForegroundColor DarkGray

    foreach ($requiredCommand in @("git", "docker")) {
        if (-not (Get-Command $requiredCommand -ErrorAction SilentlyContinue)) {
            throw "$requiredCommand was not found in PATH."
        }
    }

    Write-Step "Locating or downloading the project"
    $resolvedProjectPath = Resolve-Or-CloneProject -RequestedPath $ProjectPath
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
    $originUrl = (& git remote get-url origin).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "The Git origin remote could not be read."
    }
    if ($originUrl -notmatch "cmosantos/supportops-command-center") {
        Invoke-Native git remote set-url origin $RepositoryUrl
    }

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

    Write-Step "Building SupportOps from scratch without Docker cache"
    Invoke-Native docker compose build --pull --no-cache app

    Write-Step "Starting a fresh SupportOps container"
    Invoke-Native docker compose up -d --force-recreate app

    Write-Step "Waiting for the application health check"
    $healthUrl = "http://127.0.0.1:8501/_stcore/health"
    $ready = $false
    for ($attempt = 1; $attempt -le 60; $attempt++) {
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
        & docker compose logs --tail 100 app
        throw "SupportOps did not become healthy. The latest container logs are shown above."
    }

    Write-Step "Update completed"
    & docker compose ps
    Write-Host "SupportOps is running from commit $commit." -ForegroundColor Green
    Write-Host "The production interface is English-only." -ForegroundColor Green

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
