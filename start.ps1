$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Starting backend on http://localhost:8000 ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd '$root\backend'; ..\.venv\Scripts\Activate.ps1; uvicorn main:app --reload --port 8000"

Write-Host "Starting frontend on http://localhost:3000 ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd '$root\frontend'; npm run dev"

Write-Host ""
Write-Host "Both servers are starting in separate windows."
