[CmdletBinding()]
param(
    [ValidateSet('Auto', 'Frontend', 'Backend', 'Full')]
    [string]$Scope = 'Auto',

    [string]$Server = '124.221.19.62',

    [string]$RemoteUser = 'ubuntu',

    [string]$SshKey = (Join-Path ([Environment]::GetFolderPath('UserProfile')) '.ssh\yykitchen_deploy_ed25519'),

    [string]$RemoteDir = '/opt/yykitchen',

    [string]$PublicUrl = 'http://124.221.19.62',

    [string]$CommitMessage,

    [switch]$SkipTests,

    [switch]$DryRun,

    [switch]$Https
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$repoRoot = $PSScriptRoot
$frontendDir = Join-Path $repoRoot 'frontend'
$backendDir = Join-Path $repoRoot 'backend'
$productionEnv = Join-Path $repoRoot '.env.production'
$sshTarget = "${RemoteUser}@${Server}"
$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$releaseArchive = $null

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Invoke-Native {
    param(
        [Parameter(Mandatory)]
        [string]$FilePath,

        [Parameter()]
        [string[]]$Arguments = @(),

        [Parameter()]
        [string]$WorkingDirectory = $repoRoot
    )

    Push-Location $WorkingDirectory
    try {
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-NativeOutput {
    param(
        [Parameter(Mandatory)]
        [string]$FilePath,

        [Parameter()]
        [string[]]$Arguments = @(),

        [Parameter()]
        [string]$WorkingDirectory = $repoRoot
    )

    Push-Location $WorkingDirectory
    try {
        $output = @(& $FilePath @Arguments)
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
        }
        return $output
    }
    finally {
        Pop-Location
    }
}

function Assert-CommandExists {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Get-WorkingTreePaths {
    $paths = @()
    $paths += Invoke-NativeOutput -FilePath 'git' -Arguments @('diff', '--name-only')
    $paths += Invoke-NativeOutput -FilePath 'git' -Arguments @('diff', '--cached', '--name-only')
    $paths += Invoke-NativeOutput -FilePath 'git' -Arguments @('ls-files', '--others', '--exclude-standard')
    return @($paths | Where-Object { $_ } | Sort-Object -Unique)
}

function Get-UnsafePaths {
    param([string[]]$Paths)

    return @($Paths | Where-Object {
        $path = $_ -replace '\\', '/'
        ($path -match '(^|/)\.env($|\.)' -and $path -notmatch '\.example$') -or
        $path -match '(^|/)backend/uploads/' -or
        $path -match '(^|/)__pycache__(/|$)' -or
        $path -match '\.pyc$' -or
        $path -match '\.tar\.gz$' -or
        $path -match '\.(pem|key|p12|pfx)$' -or
        $path -match '(^|/)(id_rsa|id_ed25519)$'
    })
}

function Resolve-DeployScope {
    param([string[]]$Paths)

    if ($Scope -ne 'Auto') {
        return $Scope
    }

    $relevantPaths = @($Paths | Where-Object {
        $_ -notmatch '(^|/)(README|DEPLOYMENT)(\.[^/]+)?$' -and
        $_ -ne 'deploy.ps1' -and
        $_ -notmatch '\.md$'
    })

    if ($relevantPaths.Count -eq 0) {
        return 'None'
    }

    if (@($relevantPaths | Where-Object { $_ -notlike 'frontend/*' }).Count -eq 0) {
        return 'Frontend'
    }

    if (@($relevantPaths | Where-Object { $_ -notlike 'backend/*' }).Count -eq 0) {
        return 'Backend'
    }

    if (@($relevantPaths | Where-Object { $_ -notlike 'miniprogram/*' }).Count -eq 0) {
        return 'MiniProgramOnly'
    }

    return 'Full'
}

function Invoke-FrontendChecks {
    Write-Step 'Checking frontend'
    Invoke-Native -FilePath 'npm.cmd' -Arguments @('run', 'lint') -WorkingDirectory $frontendDir
    Invoke-Native -FilePath 'npm.cmd' -Arguments @('run', 'test') -WorkingDirectory $frontendDir
    Invoke-Native -FilePath 'npm.cmd' -Arguments @('run', 'build') -WorkingDirectory $frontendDir
}

function Invoke-BackendChecks {
    Write-Step 'Checking Java business service and Python AI service'
    Invoke-Native -FilePath 'mvn.cmd' -Arguments @('-B', '-ntp', 'verify') -WorkingDirectory (Join-Path $repoRoot 'backend-java')
    $aiPython = Join-Path $repoRoot 'ai-service/.venv/Scripts/python.exe'
    if (-not (Test-Path -LiteralPath $aiPython)) {
        throw 'Install ai-service/.venv and its dev dependencies first.'
    }
    Invoke-Native -FilePath $aiPython -Arguments @('-m', 'pytest', '-q') -WorkingDirectory (Join-Path $repoRoot 'ai-service')
}

function Invoke-ComposeCheck {
    if (-not (Test-Path -LiteralPath $productionEnv)) {
        throw "Local production environment file not found: $productionEnv"
    }

    Write-Step 'Checking production Compose configuration'
    $composeArgs = @(
        'compose', '--env-file', $productionEnv,
        '-f', (Join-Path $repoRoot 'docker-compose.prod.yml')
    )
    if (-not $Https) {
        $composeArgs += @('-f', (Join-Path $repoRoot 'docker-compose.preview.yml'))
    }
    $composeArgs += @('config', '-q')
    Invoke-Native -FilePath 'docker' -Arguments $composeArgs
}

function Get-RemoteRelease {
    $sshArgs = @(
        '-i', $SshKey,
        '-o', 'BatchMode=yes',
        '-o', 'ConnectTimeout=15',
        '-o', 'StrictHostKeyChecking=accept-new',
        $sshTarget,
        "cat '$RemoteDir/.release-version' 2>/dev/null || true"
    )
    $output = Invoke-NativeOutput -FilePath 'ssh' -Arguments $sshArgs
    return ($output -join '').Trim()
}

function Get-ChangedPathsSinceRelease {
    param([string]$RemoteRelease)

    $paths = @()
    if ($RemoteRelease) {
        & git cat-file -e "${RemoteRelease}^{commit}" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $paths += Invoke-NativeOutput -FilePath 'git' -Arguments @('diff', '--name-only', "${RemoteRelease}..HEAD")
        }
        else {
            Write-Warning "Remote release $RemoteRelease is not available locally. Falling back to a full deployment."
            $paths += @('docker-compose.prod.yml')
        }
    }
    else {
        $paths += @('docker-compose.prod.yml')
    }

    $paths += Get-WorkingTreePaths
    return @($paths | Where-Object { $_ } | Sort-Object -Unique)
}

function New-SafeReleaseArchive {
    param([string]$ShortSha)

    $script:releaseArchive = Join-Path $tempRoot "yykitchen-$ShortSha.tar.gz"
    if (Test-Path -LiteralPath $script:releaseArchive) {
        Remove-Item -LiteralPath $script:releaseArchive -Force
    }

    Write-Step 'Creating a safe release archive'
    Invoke-Native -FilePath 'git' -Arguments @('archive', '--format=tar.gz', '-o', $script:releaseArchive, 'HEAD')
    $entries = @(Invoke-NativeOutput -FilePath 'tar' -Arguments @('-tf', $script:releaseArchive))
    $unsafeEntries = @($entries | Where-Object {
        $_ -match '(^|/)(\.env|__pycache__)(/|$)' -or
        $_ -match '\.pyc$' -or
        $_ -match '\.tar\.gz$' -or
        $_ -match '^backend/uploads/'
    })
    if ($unsafeEntries.Count -gt 0) {
        throw "Release archive audit failed: $($unsafeEntries.Count) unsafe entries found."
    }

    Write-Host "Release archive audit passed: $($entries.Count) files." -ForegroundColor Green
    return $script:releaseArchive
}

function Publish-Release {
    param(
        [string]$DeployScope,
        [string]$FullSha,
        [string]$ShortSha,
        [string]$ArchivePath
    )

    $remoteArchive = "/tmp/yykitchen-$ShortSha.tar.gz"
    Write-Step 'Uploading release archive'
    Invoke-Native -FilePath 'scp' -Arguments @(
        '-i', $SshKey,
        '-o', 'BatchMode=yes',
        '-o', 'ConnectTimeout=15',
        $ArchivePath,
        "${sshTarget}:$remoteArchive"
    )

    $remoteScript = @'
set -Eeuo pipefail

scope="$1"
release_sha="$2"
remote_dir="$3"
remote_archive="$4"
mode="$5"

if [ "$(realpath "$remote_dir")" != "/opt/yykitchen" ]; then
  echo "Refusing to deploy to an unexpected directory: $remote_dir" >&2
  exit 1
fi

cd "$remote_dir"
test -f .env.production

compose=(docker compose --env-file .env.production -f docker-compose.prod.yml)
if [ "$mode" = "preview" ]; then
  compose+=(-f docker-compose.preview.yml)
fi

cleanup() {
  rm -f "$remote_archive"
}
trap cleanup EXIT

wait_for_health() {
  for attempt in $(seq 1 30); do
    if curl -fsS http://127.0.0.1/api/v1/health >/dev/null && curl -fsS http://127.0.0.1/ >/dev/null; then
      return 0
    fi
    sleep 2
  done
  return 1
}

tag_rollback_image() {
  service="$1"
  if docker image inspect "yykitchen-$service:latest" >/dev/null 2>&1; then
    docker tag "yykitchen-$service:latest" "yykitchen-$service:rollback"
  fi
}

rollback_service() {
  service="$1"
  if docker image inspect "yykitchen-$service:rollback" >/dev/null 2>&1; then
    docker tag "yykitchen-$service:rollback" "yykitchen-$service:latest"
    "${compose[@]}" up -d --no-deps --force-recreate "$service"
  fi
}

if [ "$scope" = "Backend" ] || [ "$scope" = "Full" ]; then
  mkdir -p backups
  backup_path="backups/pre-deploy-${release_sha:0:7}-$(date +%Y%m%d-%H%M%S).sql.gz"
  "${compose[@]}" exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' </dev/null | gzip -c > "$backup_path"
  test -s "$backup_path"
  echo "Database backup: $remote_dir/$backup_path"
fi

tar -xzf "$remote_archive" -C "$remote_dir"
printf '%s\n' "$release_sha" > .release-version

case "$scope" in
  Frontend)
    tag_rollback_image frontend
    "${compose[@]}" build frontend
    if ! "${compose[@]}" up -d --no-deps frontend || ! wait_for_health; then
      echo "Frontend health check failed. Restoring the previous image." >&2
      rollback_service frontend
      exit 1
    fi
    ;;
  Backend)
    tag_rollback_image backend
    "${compose[@]}" build backend
    if ! "${compose[@]}" up -d --no-deps backend || ! wait_for_health; then
      echo "Backend health check failed. Restoring the previous image." >&2
      rollback_service backend
      exit 1
    fi
    ;;
  Full)
    tag_rollback_image frontend
    tag_rollback_image backend
    if ! "${compose[@]}" up -d --build --remove-orphans || ! wait_for_health; then
      echo "Release health check failed. Restoring previous images." >&2
      rollback_service backend
      rollback_service frontend
      exit 1
    fi
    ;;
  *)
    echo "Unknown deployment scope: $scope" >&2
    exit 1
    ;;
esac

"${compose[@]}" ps
echo "release=$release_sha"
echo "health=ok"
'@

    if ($DeployScope -ne 'Frontend') {
        $remoteScript = @'
set -Eeuo pipefail
release_sha="$2"
remote_dir="$3"
remote_archive="$4"
mode="$5"
[[ "$(realpath "$remote_dir")" == "/opt/yykitchen" ]]
[[ "$release_sha" =~ ^[0-9a-f]{40}$ ]]
[[ "$remote_archive" == /tmp/yykitchen-*.tar.gz ]]
cd "$remote_dir"
test -f .env.production
tar -xzf "$remote_archive" -C "$remote_dir"
bash scripts/deploy-services.sh "$mode" deploy
printf '%s\n' "$release_sha" > .release-version
'@
    }
    $mode = if ($Https) { 'https' } else { 'preview' }
    $sshArgs = @(
        '-i', $SshKey,
        '-o', 'BatchMode=yes',
        '-o', 'ConnectTimeout=15',
        $sshTarget,
        'bash', '-s', '--',
        $DeployScope, $FullSha, $RemoteDir, $remoteArchive, $mode
    )

    Write-Step "Deploying $DeployScope"
    $remoteScript | & ssh @sshArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Server deployment failed with exit code $LASTEXITCODE."
    }

    $verifiedRelease = Get-RemoteRelease
    if ($verifiedRelease -ne $FullSha) {
        throw "Server release verification failed. Expected $FullSha, got '$verifiedRelease'."
    }
}

try {
    Set-Location $repoRoot

    foreach ($command in @('git', 'tar', 'npm.cmd')) {
        Assert-CommandExists $command
    }

    if (-not $DryRun) {
        foreach ($command in @('ssh', 'scp')) {
            Assert-CommandExists $command
        }
        if (-not (Test-Path -LiteralPath $SshKey)) {
            throw "SSH private key not found: $SshKey"
        }
    }

    $branch = (Invoke-NativeOutput -FilePath 'git' -Arguments @('branch', '--show-current') | Select-Object -First 1).Trim()
    if ($branch -ne 'main') {
        throw "Production deployment is allowed only from main. Current branch: $branch"
    }

    $workingPaths = @(Get-WorkingTreePaths)
    $unsafeWorkingPaths = @(Get-UnsafePaths -Paths $workingPaths)
    if ($unsafeWorkingPaths.Count -gt 0) {
        throw "Unsafe files detected:`n$($unsafeWorkingPaths -join "`n")"
    }

    if ($DryRun) {
        Write-Step 'Dry run'
        if ($workingPaths.Count -gt 0) {
            Write-Host 'These uncommitted changes are not included in the dry-run archive:'
            $workingPaths | ForEach-Object { Write-Host "  $_" }
        }
    }
    elseif ($workingPaths.Count -gt 0) {
        Write-Step 'Reviewing local changes'
        Invoke-Native -FilePath 'git' -Arguments @('status', '--short')
        $confirmation = Read-Host 'Stage and commit all changes above? Enter y to continue'
        if ($confirmation -notin @('y', 'Y', 'yes', 'YES')) {
            throw 'Deployment cancelled.'
        }

        Invoke-Native -FilePath 'git' -Arguments @('add', '--all')
        $stagedPaths = @(Invoke-NativeOutput -FilePath 'git' -Arguments @('diff', '--cached', '--name-only'))
        $unsafeStagedPaths = @(Get-UnsafePaths -Paths $stagedPaths)
        if ($unsafeStagedPaths.Count -gt 0) {
            throw "Unsafe files found in the staging area:`n$($unsafeStagedPaths -join "`n")"
        }
    }

    $remoteRelease = if ($DryRun) { '' } else {
        Write-Step 'Reading the current server release'
        Get-RemoteRelease
    }

    $changedPaths = @(
        if ($DryRun) {
            Get-WorkingTreePaths
        }
        else {
            Get-ChangedPathsSinceRelease -RemoteRelease $remoteRelease
        }
    )
    $deployScope = Resolve-DeployScope -Paths $changedPaths

    if ($deployScope -eq 'MiniProgramOnly') {
        throw 'Only miniprogram files changed. Publish them with WeChat DevTools instead of this website deployment script.'
    }

    Write-Host "Deployment scope: $deployScope" -ForegroundColor Yellow
    if ($changedPaths.Count -gt 0) {
        Write-Host 'Detected changes:'
        $changedPaths | ForEach-Object { Write-Host "  $_" }
    }

    if (-not $SkipTests) {
        if ($deployScope -in @('Frontend', 'Full')) {
            Invoke-FrontendChecks
        }
        if ($deployScope -in @('Backend', 'Full')) {
            Invoke-BackendChecks
        }
        if ($deployScope -in @('Backend', 'Full')) {
            Invoke-ComposeCheck
        }
    }
    else {
        Write-Warning 'Tests were skipped by request.'
    }

    if (-not $DryRun -and $workingPaths.Count -gt 0) {
        if (-not $CommitMessage) {
            $defaultMessage = "Release $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
            $enteredMessage = Read-Host "Commit message (press Enter to use: $defaultMessage)"
            $CommitMessage = if ([string]::IsNullOrWhiteSpace($enteredMessage)) { $defaultMessage } else { $enteredMessage }
        }
        Invoke-Native -FilePath 'git' -Arguments @('commit', '-m', $CommitMessage)
    }

    $fullSha = (Invoke-NativeOutput -FilePath 'git' -Arguments @('rev-parse', 'HEAD') | Select-Object -First 1).Trim()
    $shortSha = (Invoke-NativeOutput -FilePath 'git' -Arguments @('rev-parse', '--short=7', 'HEAD') | Select-Object -First 1).Trim()
    $archivePath = New-SafeReleaseArchive -ShortSha $shortSha

    if ($DryRun) {
        Write-Host "`nDry run passed: $shortSha ($deployScope). Nothing was committed, pushed, or uploaded." -ForegroundColor Green
        exit 0
    }

    Write-Step 'Pushing to GitHub'
    Invoke-Native -FilePath 'git' -Arguments @('push', 'origin', 'main')

    if ($deployScope -eq 'None') {
        Write-Host 'Only documentation or deployment tooling changed. No application rebuild is needed.' -ForegroundColor Green
        exit 0
    }

    Publish-Release -DeployScope $deployScope -FullSha $fullSha -ShortSha $shortSha -ArchivePath $archivePath

    Write-Step 'Running public smoke checks'
    $healthUrl = "$($PublicUrl.TrimEnd('/'))/api/v1/health"
    $rootResponse = Invoke-WebRequest -UseBasicParsing -Uri $PublicUrl -TimeoutSec 20
    $healthResponse = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 20
    if ($rootResponse.StatusCode -ne 200 -or $healthResponse.StatusCode -ne 200) {
        throw "Public smoke checks failed: root $($rootResponse.StatusCode), API $($healthResponse.StatusCode)."
    }

    Write-Host "`nDeployment succeeded: $shortSha ($deployScope)" -ForegroundColor Green
    Write-Host "Public URL: $PublicUrl"
}
finally {
    if ($releaseArchive -and (Test-Path -LiteralPath $releaseArchive)) {
        $resolvedArchive = [System.IO.Path]::GetFullPath($releaseArchive)
        if ($resolvedArchive.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            Remove-Item -LiteralPath $resolvedArchive -Force
        }
    }
    Set-Location $repoRoot
}
