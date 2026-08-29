import asyncio
import uuid
from pathlib import PurePosixPath

from supabase import create_client

from config import settings
from schemas.release_notes import ReleaseNoteCreate, ReleaseNoteUpdate

TABLE = "release_notes"
BUCKET = "release-notes"

# Illustrations are screenshots or short GIFs, not photo libraries.
MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def _client():
    # Same rationale as db.supabase_client: a fresh client per call keeps
    # concurrent asyncio.to_thread calls off a shared HTTP/2 connection.
    return create_client(settings.supabase_url, settings.supabase_api_key)


def _list() -> list[dict]:
    return (
        _client()
        .table(TABLE)
        .select("*")
        .order("published_at", desc=True)
        .execute()
        .data
    )


def _create(payload: dict) -> dict:
    return _client().table(TABLE).insert(payload).execute().data[0]


def _update(note_id: str, payload: dict) -> list[dict]:
    return _client().table(TABLE).update(payload).eq("id", note_id).execute().data


def _delete(note_id: str) -> list[dict]:
    return _client().table(TABLE).delete().eq("id", note_id).execute().data


def _upload(path: str, content: bytes, content_type: str) -> str:
    client = _client()
    client.storage.from_(BUCKET).upload(
        path, content, {"content-type": content_type, "upsert": "false"}
    )
    return client.storage.from_(BUCKET).get_public_url(path)


def _serialize(note: ReleaseNoteCreate | ReleaseNoteUpdate, partial: bool) -> dict:
    payload = note.model_dump(exclude_none=partial, mode="json")
    # published_at is optional on create: the table defaults it to now()
    if payload.get("published_at") is None:
        payload.pop("published_at", None)
    return payload


async def list_release_notes() -> list[dict]:
    return await asyncio.to_thread(_list)


async def create_release_note(note: ReleaseNoteCreate) -> dict:
    return await asyncio.to_thread(_create, _serialize(note, partial=False))


async def update_release_note(note_id: str, note: ReleaseNoteUpdate) -> dict | None:
    payload = _serialize(note, partial=True)
    if not payload:
        return None
    rows = await asyncio.to_thread(_update, note_id, payload)
    return rows[0] if rows else None


async def delete_release_note(note_id: str) -> bool:
    rows = await asyncio.to_thread(_delete, note_id)
    return bool(rows)


async def upload_image(filename: str, content: bytes, content_type: str) -> str:
    """Store an illustration in the public release-notes bucket, return its URL."""
    extension = ALLOWED_IMAGE_TYPES[content_type]
    # Keep the original stem for recognisable filenames, but never trust it as a path
    stem = PurePosixPath(filename or "image").stem[:40] or "image"
    safe_stem = "".join(char if char.isalnum() or char in "-_" else "-" for char in stem)
    path = f"{uuid.uuid4().hex[:8]}-{safe_stem}{extension}"
    return await asyncio.to_thread(_upload, path, content, content_type)
