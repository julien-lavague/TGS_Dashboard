# /start_tgsdashboard

Start the TGS Dashboard backend and frontend, verify both are healthy, and auto-fix any startup errors. Retry up to 3 times before giving up.

---

## Phase 1 — Start both servers

Use PowerShell to run each server as a background job so their output can be captured. Use the project root `C:\Users\julie\Documents\DEV\tgs-dashboard` as the base.

**Backend job:**
```powershell
Start-Job -Name "TGS-Backend" -ScriptBlock {
    Set-Location "C:\Users\julie\Documents\DEV\tgs-dashboard\backend"
    & "..\..\.venv\Scripts\python.exe" -m uvicorn main:app --reload --port 8000 2>&1
}
```

**Frontend job:**
```powershell
Start-Job -Name "TGS-Frontend" -ScriptBlock {
    Set-Location "C:\Users\julie\Documents\DEV\tgs-dashboard\frontend"
    npm run dev 2>&1
}
```

Tell the user: "Starting backend (port 8000) and frontend (port 3000)..."

Wait 5 seconds for initial startup.

---

## Phase 2 — Health checks

### Backend
Poll `http://localhost:8000/health` every 3 seconds for up to 30 seconds using:
```powershell
try { (Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2).StatusCode } catch { $null }
```
Expect status `200` and a response body containing `"ok"`.

### Frontend
Poll `http://localhost:3000` every 5 seconds for up to 90 seconds (Next.js compilation takes time):
```powershell
try { (Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 3).StatusCode } catch { $null }
```
Expect status `200`.

If both checks pass → report success:
```
✓ Backend:  http://localhost:8000  (health: ok)
✓ Frontend: http://localhost:3000
Both servers are running.
```
Then stop — do not proceed to Phase 3.

---

## Phase 3 — Error diagnosis and fix loop (max 3 attempts)

If either server does not respond within its timeout, or if a job exits prematurely:

### Step 1 — Collect output
```powershell
Receive-Job -Name "TGS-Backend" -Keep
Receive-Job -Name "TGS-Frontend" -Keep
```

### Step 2 — Analyze the error
Read the captured output carefully. Common errors and their fixes:

| Error pattern | Fix |
|---|---|
| `SettingsError: error parsing value for field "cors_origins"` | Update `.env`: wrap value in JSON array `["..."]` |
| `JSONDecodeError` on any `.env` list field | Same — wrap the value in `["..."]` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` from `backend/` |
| `ImportError` | Check the import path and fix it in the relevant `.py` file |
| `uvicorn: error` / port already in use | Kill existing process: `Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force` |
| Next.js `Module not found` | Run `npm install` in `frontend/` |
| TypeScript / type error in frontend | Find the file and line number from the error, fix the type |
| `SyntaxError` in Python | Find the file and line number from the traceback, fix the syntax |

Apply the fix directly to the source files.

### Step 3 — Stop failed job(s)
```powershell
Stop-Job  -Name "TGS-Backend"  -ErrorAction SilentlyContinue
Remove-Job -Name "TGS-Backend"  -ErrorAction SilentlyContinue
Stop-Job  -Name "TGS-Frontend" -ErrorAction SilentlyContinue
Remove-Job -Name "TGS-Frontend" -ErrorAction SilentlyContinue
```

### Step 4 — Restart
Go back to **Phase 1**. Track the attempt number (1, 2, 3).

Tell the user which attempt this is: `"Fix applied. Restarting (attempt 2/3)..."`

### Retry limit
After **3 failed attempts**, stop the loop and report:
- The full captured output from the last failed run
- A summary of all fixes attempted
- Ask the user how to proceed
