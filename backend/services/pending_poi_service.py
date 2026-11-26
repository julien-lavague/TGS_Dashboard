"""POI submitted by users and waiting for an admin to validate them.

Each source is a Supabase table with a `status` text column where 'pending'
means "awaiting admin review" (the TheGoodSpots admin reads them the same way).
"""

import asyncio
from datetime import datetime, timezone

from supabase import create_client

from config import settings

# key -> (table, label, columns used to describe one item)
SOURCES: dict[str, dict] = {
    "spots": {
        "table": "spots_add",
        "label": "Spots proposés",
        "columns": "id, name, departement_name, submitted_by_email, created_at",
        "title": lambda r: r.get("name") or "Spot sans nom",
        "subtitle": lambda r: " · ".join(
            x for x in (r.get("departement_name"), r.get("submitted_by_email")) if x
        ),
    },
    "nautical_restrictions": {
        "table": "nautical_restrictions",
        "label": "Restrictions nautiques",
        "columns": "id, description, entity_name, declarant_name, start_date, end_date, created_at",
        "title": lambda r: r.get("entity_name") or r.get("declarant_name") or "Restriction",
        "subtitle": lambda r: " · ".join(
            x
            for x in (
                f"du {r['start_date']} au {r['end_date']}" if r.get("start_date") and r.get("end_date") else None,
                (r.get("description") or "")[:80] or None,
            )
            if x
        ),
    },
}

ADMIN_URL = "https://thegoodspots.fr/admin"


def _fetch(table: str, columns: str) -> list[dict]:
    # A fresh client per call, see db.supabase_client.
    client = create_client(settings.supabase_url, settings.supabase_api_key)
    return (
        client.table(table)
        .select(columns)
        .eq("status", "pending")
        .order("created_at", desc=False)
        .execute()
        .data
    )


async def get_pending_poi() -> dict:
    keys = list(SOURCES)
    results = await asyncio.gather(
        *(asyncio.to_thread(_fetch, SOURCES[k]["table"], SOURCES[k]["columns"]) for k in keys),
        return_exceptions=True,
    )

    groups: list[dict] = []
    for key, result in zip(keys, results):
        src = SOURCES[key]
        if isinstance(result, Exception):
            groups.append({"key": key, "label": src["label"], "count": None, "error": str(result), "items": []})
            continue
        groups.append({
            "key": key,
            "label": src["label"],
            "count": len(result),
            "error": None,
            # Oldest first: what has been waiting the longest.
            "items": [
                {
                    "id": r["id"],
                    "title": src["title"](r),
                    "subtitle": src["subtitle"](r) or None,
                    "created_at": r.get("created_at"),
                }
                for r in result
            ],
        })

    return {
        "total": sum(g["count"] or 0 for g in groups),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "admin_url": ADMIN_URL,
        "groups": groups,
    }
