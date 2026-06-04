import os
import aiofiles

# Local storage directory
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def upload_resume(file_bytes: bytes, candidate_id: str, original_filename: str = "") -> str:
    """Save a resume PDF/image to local storage and return the file key/path."""
    # Preserve the real extension so OCR vs PDF routing works correctly downstream
    import os as _os
    ext = _os.path.splitext(original_filename.lower())[1] if original_filename else ".pdf"
    if ext not in {".pdf", ".png", ".jpg", ".jpeg"}:
        ext = ".pdf"
    filename = f"{candidate_id}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(file_bytes)
    return filename  # This is the "key" — just the filename


async def download_resume(key: str) -> bytes:
    """Read a resume from local storage."""
    filepath = os.path.join(UPLOAD_DIR, key)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Resume not found: {key}")
    async with aiofiles.open(filepath, "rb") as f:
        return await f.read()


async def delete_resume(key: str):
    """Delete a resume from local storage."""
    filepath = os.path.join(UPLOAD_DIR, key)
    if os.path.exists(filepath):
        os.remove(filepath)


async def generate_presigned_url(key: str, expiration: int = 3600) -> str:
    """For local storage, just return the API endpoint to fetch the file."""
    return f"/api/candidates/file/{key}"