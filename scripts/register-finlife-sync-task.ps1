param(
    [string]$TaskName = "StudyRag-FinlifeCompanySync",
    [string]$StartAt = "03:00"
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv-win\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Windows virtual environment was not found: $Python"
}

$Action = New-ScheduledTaskAction `
    -Execute $Python `
    -Argument "-m app.jobs.finlife_company_sync --trigger scheduled" `
    -WorkingDirectory $ProjectRoot
$Trigger = New-ScheduledTaskTrigger -Daily -At $StartAt

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Description "Synchronize Finlife company data and pgvector embeddings." `
    -Force

Write-Host "Registered $TaskName to run daily at $StartAt."
