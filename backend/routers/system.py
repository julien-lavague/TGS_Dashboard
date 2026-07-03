import os
import time
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks

router = APIRouter(prefix="/api/system", tags=["system"])

# A dedicated .py file inside the backend dir. Rewriting it changes its mtime,
# which uvicorn's `--reload` watcher picks up and uses to restart the server.
# The file is never imported, so its contents have no runtime effect.
_SENTINEL = Path(__file__).resolve().parent.parent / "_reload_sentinel.py"


@router.get("/health")
async def health():
    return {"status": "ok"}


def _trigger_reload() -> None:
    # Give the HTTP response time to reach the client before the worker is
    # torn down and respawned by the reloader.
    time.sleep(0.4)
    _SENTINEL.write_text(
        f"# Auto-generated restart trigger. Touched at {time.time()}\n",
        encoding="utf-8",
    )
    # Bump mtime explicitly in case the content is unchanged.
    os.utime(_SENTINEL, None)


@router.post("/restart")
async def restart(background_tasks: BackgroundTasks):
    """Restart the backend by tripping uvicorn's --reload file watcher.

    Only effective when the server is run with `uvicorn ... --reload`
    (the dev setup). Without --reload this is a no-op.
    """
    background_tasks.add_task(_trigger_reload)
    return {"restarting": True}
