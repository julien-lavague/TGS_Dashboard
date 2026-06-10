from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers import alerts, overview, usage, profils, users, equipments

app = FastAPI(title="TGS Metrics Dashboard", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts.router)
app.include_router(overview.router)
app.include_router(usage.router)
app.include_router(profils.router)
app.include_router(users.router)
app.include_router(equipments.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
