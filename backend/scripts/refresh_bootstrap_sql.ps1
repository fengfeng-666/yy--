param(
    [string]$OutputPath = "sql/bootstrap_schema.generated.sql"
)

$ErrorActionPreference = "Stop"

$backendRoot = Split-Path -Parent $PSScriptRoot
Set-Location $backendRoot

$outputFile = Join-Path $backendRoot $OutputPath
$outputDirectory = Split-Path -Parent $outputFile

if (-not (Test-Path $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory | Out-Null
}

$sql = uv run alembic upgrade head --sql
$sql | Out-File -FilePath $outputFile -Encoding utf8

Write-Host "SQL 快照已生成：" $outputFile
