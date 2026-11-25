"""Health of the TheGoodSpots workloads running on Google Cloud.

Talks to the GCP REST APIs directly (Cloud Run Admin v2, Cloud Scheduler v1).

Credentials, first match wins:
  1. GCP_SERVICE_ACCOUNT_JSON  -- the service-account key, as raw JSON or
     base64 (this is what Railway uses)
  2. Application Default Credentials (GOOGLE_APPLICATION_CREDENTIALS, ...)
  3. `gcloud auth print-access-token` -- local dev with a logged-in gcloud

Covers:
  - Cloud Run jobs     -> status of the latest execution
  - Cloud Run services -> Ready condition
  - Cloud Scheduler    -> result of the last trigger attempt
"""

import asyncio
import base64
import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from config import settings

_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
_RUN = "https://run.googleapis.com/v2"
_SCHEDULER = "https://cloudscheduler.googleapis.com/v1"

_CACHE_TTL_S = 60
_cache: dict[str, Any] = {"at": 0.0, "data": None}
_credentials: Any = None


class GcpError(RuntimeError):
    pass


# --------------------------------------------------------------------------- auth

def _load_credentials() -> Any:
    raw = settings.gcp_service_account_json.strip()
    if raw:
        from google.oauth2 import service_account

        if not raw.startswith("{"):
            raw = base64.b64decode(raw).decode("utf-8")
        return service_account.Credentials.from_service_account_info(json.loads(raw), scopes=_SCOPES)
    try:
        import google.auth

        creds, _ = google.auth.default(scopes=_SCOPES)
        return creds
    except Exception:
        return None


def _gcloud_token() -> str:
    exe = shutil.which("gcloud")
    if not exe:
        raise GcpError(
            "Aucun identifiant GCP : définir GCP_SERVICE_ACCOUNT_JSON (ou installer gcloud en local)"
        )
    proc = subprocess.run([exe, "auth", "print-access-token"], capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise GcpError(proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "gcloud auth a échoué")
    return proc.stdout.strip()


def _access_token() -> str:
    global _credentials
    if _credentials is None:
        _credentials = _load_credentials() or "gcloud"
    if _credentials == "gcloud":
        return _gcloud_token()
    if not _credentials.valid:
        from google.auth.transport.requests import Request

        _credentials.refresh(Request())
    return _credentials.token


# --------------------------------------------------------------------------- http

async def _get(client: httpx.AsyncClient, url: str, list_key: str | None = None) -> Any:
    """GET a resource, or every page of a list when `list_key` is given."""
    items: list = []
    params: dict[str, str] = {}
    while True:
        resp = await client.get(url, params=params)
        if resp.status_code >= 400:
            try:
                msg = resp.json()["error"]["message"]
            except Exception:
                msg = resp.reason_phrase or "réponse inattendue"
            raise GcpError(f"HTTP {resp.status_code} : {msg}")
        body = resp.json()
        if list_key is None:
            return body
        items.extend(body.get(list_key, []))
        token = body.get("nextPageToken")
        if not token:
            return items
        params = {"pageToken": token}


def _short(name: str) -> str:
    return name.rsplit("/", 1)[-1]


def _failed_condition_message(conditions: list[dict]) -> str | None:
    for cond in conditions or []:
        if cond.get("type") == "Completed" and cond.get("state") == "CONDITION_FAILED":
            return cond.get("message")
    for cond in conditions or []:
        if cond.get("state") == "CONDITION_FAILED" and cond.get("message"):
            return cond["message"]
    return None


# --------------------------------------------------------------------------- sources

async def _jobs(client: httpx.AsyncClient, parent: str) -> list[dict]:
    jobs = await _get(client, f"{_RUN}/{parent}/jobs", "jobs")

    async def one(job: dict) -> dict:
        latest = job.get("latestCreatedExecution") or {}
        completion = latest.get("completionStatus")
        if not latest:
            status, detail = "unknown", "Aucune exécution"
        elif completion == "EXECUTION_SUCCEEDED":
            status, detail = "ok", None
        elif completion in ("EXECUTION_FAILED", "EXECUTION_CANCELLED"):
            status = "error"
            try:
                # v2 returns the short execution id here, not a full resource path.
                ex = await _get(client, f"{_RUN}/{job['name']}/executions/{_short(latest['name'])}")
                detail = _failed_condition_message(ex.get("conditions", [])) or completion
            except GcpError as exc:
                detail = str(exc)
            if completion == "EXECUTION_CANCELLED":
                detail = f"Exécution annulée. {detail}"
        else:
            status, detail = "running", "Exécution en cours"
        return {
            "name": _short(job["name"]),
            "kind": "Cloud Run job",
            "status": status,
            "detail": detail,
            "last_run": latest.get("completionTime") or latest.get("createTime"),
            "execution": _short(latest["name"]) if latest.get("name") else None,
        }

    return list(await asyncio.gather(*(one(j) for j in jobs)))


async def _services(client: httpx.AsyncClient, parent: str) -> list[dict]:
    services = await _get(client, f"{_RUN}/{parent}/services", "services")
    items: list[dict] = []
    for svc in services:
        ready = svc.get("terminalCondition") or {}
        ok = ready.get("state") == "CONDITION_SUCCEEDED"
        items.append({
            "name": _short(svc["name"]),
            "kind": "Cloud Run service",
            "status": "ok" if ok else "error",
            "detail": None if ok else (ready.get("message") or _failed_condition_message(svc.get("conditions", []))),
            "last_run": ready.get("lastTransitionTime"),
            "execution": None,
        })
    return items


async def _schedulers(client: httpx.AsyncClient, parent: str) -> list[dict]:
    jobs = await _get(client, f"{_SCHEDULER}/{parent}/jobs", "jobs")
    items: list[dict] = []
    for job in jobs:
        # `status` is a google.rpc.Status of the last attempt: {} means success.
        rpc = job.get("status") or {}
        if rpc.get("code"):
            status = "error"
            detail = rpc.get("message") or f"Code d'erreur {rpc['code']}"
        elif job.get("state") != "ENABLED":
            status, detail = "unknown", f"Planificateur {job.get('state', '').lower()}"
        else:
            status, detail = "ok", None
        items.append({
            "name": _short(job["name"]),
            "kind": "Cloud Scheduler",
            "status": status,
            "detail": detail,
            "last_run": job.get("lastAttemptTime"),
            "execution": job.get("schedule"),
        })
    return items


# --------------------------------------------------------------------------- entry point

async def get_gcp_status(force: bool = False) -> dict:
    now = time.monotonic()
    if not force and _cache["data"] and now - _cache["at"] < _CACHE_TTL_S:
        return _cache["data"]

    items: list[dict] = []
    errors: list[dict] = []
    try:
        token = await asyncio.to_thread(_access_token)
    except Exception as exc:
        errors.append({"source": "Authentification GCP", "message": str(exc)})
    else:
        parent = f"projects/{settings.gcp_project}/locations/{settings.gcp_region}"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(headers=headers, timeout=30) as client:
            sources = {
                "Cloud Run jobs": _jobs(client, parent),
                "Cloud Run services": _services(client, parent),
                "Cloud Scheduler": _schedulers(client, parent),
            }
            results = await asyncio.gather(*sources.values(), return_exceptions=True)
        for label, result in zip(sources, results):
            if isinstance(result, Exception):
                errors.append({"source": label, "message": str(result)})
            else:
                items.extend(result)

    # Errors first, then by name.
    order = {"error": 0, "running": 1, "unknown": 2, "ok": 3}
    items.sort(key=lambda i: (order.get(i["status"], 9), i["name"]))

    data = {
        "project": settings.gcp_project,
        "region": settings.gcp_region,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "items": items,
        "source_errors": errors,
    }
    # Don't pin an auth failure for a whole TTL.
    if not errors:
        _cache.update(at=now, data=data)
    return data
