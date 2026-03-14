import magic
from fastapi import HTTPException, UploadFile

BLOCKED_MIME_TYPES = {
    "application/x-dosexec", "application/x-msdownload",
    "application/x-sharedlib", "application/x-object",
}
MAX_FILE_SIZE = 500 * 1024 * 1024

async def validate_file(file: UploadFile) -> tuple[bytes, str]:
    header = await file.read(8192)
    if not header:
        return b"", "application/octet-stream"
    detected_mime = magic.from_buffer(header, mime=True)
    if detected_mime in BLOCKED_MIME_TYPES:
        raise HTTPException(status_code=415, detail=f"File type '{detected_mime}' is blocked.")
    rest = await file.read()
    content = header + rest
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 500MB.")
    return content, detected_mime
