$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Starting backend on http://localhost:8000 ..."
# WATCHFILES_FORCE_POLLING: native FS events are often missed under OneDrive-synced
# Windows paths, so --reload silently never fires. Polling reliably picks up edits.
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd '$root\backend'; ..\.venv\Scripts\Activate.ps1; `$env:WATCHFILES_FORCE_POLLING='true'; `$env:WATCHFILES_POLL_DELAY_MS='1000'; uvicorn main:app --reload --reload-dir '$root\backend' --port 8000"

Write-Host "Starting frontend on http://localhost:3000 ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd '$root\frontend'; npm run dev"

Write-Host ""
Write-Host "Both servers are starting in separate windows."
