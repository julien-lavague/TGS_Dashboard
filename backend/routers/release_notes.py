from fastapi import APIRouter, File, HTTPException, UploadFile

from schemas.release_notes import (
    ImageUploadResponse,
    ReleaseNote,
    ReleaseNoteCreate,
    ReleaseNotesResponse,
    ReleaseNoteUpdate,
)
from services.release_notes_service import (
    ALLOWED_IMAGE_TYPES,
    MAX_IMAGE_BYTES,
    create_release_note,
    delete_release_note,
    list_release_notes,
    update_release_note,
    upload_image,
)

router = APIRouter(prefix="/api/release-notes", tags=["release-notes"])


@router.get("", response_model=ReleaseNotesResponse)
async def list_notes():
    rows = await list_release_notes()
    return ReleaseNotesResponse(rows=rows)


@router.post("", response_model=ReleaseNote, status_code=201)
async def create_note(note: ReleaseNoteCreate):
    try:
        return await create_release_note(note)
    except Exception as error:  # noqa: BLE001 - surface the Postgres message as-is
        message = str(error)
        # release_notes.version is unique: publishing twice is a user error, not a 500
        if "duplicate key" in message or "release_notes_version_key" in message:
            raise HTTPException(status_code=409, detail=f"Version {note.version} already published")
        raise HTTPException(status_code=502, detail=message)


@router.patch("/{note_id}", response_model=ReleaseNote)
async def patch_note(note_id: str, note: ReleaseNoteUpdate):
    updated = await update_release_note(note_id, note)
    if updated is None:
        raise HTTPException(status_code=404, detail="Release note not found")
    return updated


@router.delete("/{note_id}", status_code=204)
async def remove_note(note_id: str):
    if not await delete_release_note(note_id):
        raise HTTPException(status_code=404, detail="Release note not found")


@router.post("/images", response_model=ImageUploadResponse)
async def upload_illustration(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported type {file.content_type}. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )

    content = await file.read()
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Image too large ({len(content)} bytes, max {MAX_IMAGE_BYTES})",
        )

    try:
        url = await upload_image(file.filename or "image", content, file.content_type)
    except Exception as error:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(error))

    return ImageUploadResponse(image_url=url)
