# Windows 작업 스케줄러에 Finlife 동기화 배치를 등록하는 스크립트입니다.
# ``.venv-win``의 Python으로 ``app.jobs.finlife_company_sync``를 매일 실행하며,
# 실행 결과는 DB의 ``takhyeong_saving_log``에 ``scheduled`` 유형으로 기록됩니다.
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
