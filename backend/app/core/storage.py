import os, uuid
import aiofiles
import aioboto3
from botocore.client import Config
from fastapi import HTTPException
from app.config import settings

def _s3_session():
    return aioboto3.Session(
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
    )

def _stored_name(original: str) -> str:
    ext = os.path.splitext(original)[1].lower()
    return f"{uuid.uuid4().hex}{ext}"

async def save_file(content: bytes, original_filename: str, repo_id: int) -> tuple[str, str]:
    stored_name = _stored_name(original_filename)
    storage_path = f"repos/{repo_id}/{stored_name}"
    if settings.STORAGE_BACKEND == "s3":
        async with _s3_session().client("s3", endpoint_url=settings.S3_ENDPOINT_URL, config=Config(signature_version="s3v4")) as s3:
            try:
                await s3.put_object(Bucket=settings.S3_BUCKET_NAME, Key=storage_path, Body=content, ContentDisposition=f'attachment; filename="{original_filename}"')
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Storage error: {e}")
    else:
        full_dir = os.path.join(settings.LOCAL_STORAGE_PATH, "repos", str(repo_id))
        os.makedirs(full_dir, exist_ok=True)
        async with aiofiles.open(os.path.join(full_dir, stored_name), "wb") as f:
            await f.write(content)
    return stored_name, storage_path

async def delete_file(storage_path: str) -> None:
    if settings.STORAGE_BACKEND == "s3":
        async with _s3_session().client("s3", endpoint_url=settings.S3_ENDPOINT_URL, config=Config(signature_version="s3v4")) as s3:
            try:
                await s3.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=storage_path)
            except Exception:
                pass
    else:
        full = os.path.join(settings.LOCAL_STORAGE_PATH, storage_path)
        if os.path.exists(full):
            os.remove(full)

async def get_file_content(storage_path: str) -> bytes:
    if settings.STORAGE_BACKEND == "s3":
        async with _s3_session().client("s3", endpoint_url=settings.S3_ENDPOINT_URL, config=Config(signature_version="s3v4")) as s3:
            try:
                r = await s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=storage_path)
                return await r["Body"].read()
            except Exception:
                raise HTTPException(status_code=404, detail="File not found in storage")
    else:
        full = os.path.join(settings.LOCAL_STORAGE_PATH, storage_path)
        if not os.path.exists(full):
            raise HTTPException(status_code=404, detail="File not found")
        async with aiofiles.open(full, "rb") as f:
            return await f.read()

async def get_presigned_url(storage_path: str, original_filename: str, expires: int = 3600) -> str | None:
    if settings.STORAGE_BACKEND != "s3":
        return None
    async with _s3_session().client("s3", endpoint_url=settings.S3_ENDPOINT_URL, config=Config(signature_version="s3v4")) as s3:
        try:
            return await s3.generate_presigned_url("get_object", Params={"Bucket": settings.S3_BUCKET_NAME, "Key": storage_path, "ResponseContentDisposition": f'attachment; filename="{original_filename}"'}, ExpiresIn=expires)
        except Exception:
            return None
