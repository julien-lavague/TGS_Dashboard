from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from auth import require_login
from routers import alerts, overview, usage, profils, users, equipments, system

app = FastAPI(title="TGS Metrics Dashboard", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Every data router requires HTTP Basic auth (DASHBOARD_USER / DASHBOARD_PASSWORD).
# /health below is intentionally left open for platform health checks.
_auth = [Depends(require_login)]

app.include_router(alerts.router, dependencies=_auth)
app.include_router(overview.router, dependencies=_auth)
app.include_router(usage.router, dependencies=_auth)
app.include_router(profils.router, dependencies=_auth)
app.include_router(users.router, dependencies=_auth)
app.include_router(equipments.router, dependencies=_auth)
app.include_router(system.router, dependencies=_auth)


@app.get("/health")
async def health():
    return {"status": "ok"}
