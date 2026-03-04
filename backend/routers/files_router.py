    # backend/routers/files_router.py
from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, HTTPException, Request
from sqlalchemy.orm import Session
import magic
from database import get_db
from models import User, Repository, File
from route.auth_router import get_current_user
from s3_utils import upload_to_s3, delete_from_s3
from main import limiter # Import limiter for this route

router = APIRouter(prefix="/api/files", tags=["Files & PRs"])

@router.post("/{repo_id}/upload")
@limiter.limit("20/minute")
async def upload_file(request: Request, repo_id: str, file: UploadFile = FastAPIFile(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo: raise HTTPException(status_code=404, detail="Repo not found")

    file_bytes = await file.read()
    file_size = len(file_bytes)
    
    # If owner is uploading, check storage quota
    is_owner = (repo.owner_id == current_user.id)
    if is_owner and (current_user.storage_used + file_size > current_user.storage_limit):
        raise HTTPException(status_code=402, detail="QUOTA_EXCEEDED")

    mime_type = magic.from_buffer(file_bytes, mime=True)
    is_raw = mime_type.startswith('text/') or file.filename.endswith(('.sh', '.py', '.md'))
    s3_key = f"{repo.owner.username}/{repo.name}/{file.filename}"
    
    await file.seek(0)
    if not upload_to_s3(file.file, s3_key, mime_type):
        raise HTTPException(status_code=500, detail="Storage Upload Failed")

    # If non-owner uploads, it becomes a Pull Request
    status_val = "APPROVED" if is_owner else "PENDING_REVIEW"
    
    new_file = File(repo_id=repo.id, uploader_id=current_user.id, filename=file.filename, s3_key=s3_key, file_size=file_size, is_raw=is_raw, status=status_val)
    db.add(new_file)
    
    if is_owner:
        current_user.storage_used += file_size
        
    db.commit()
    return {"message": "Upload successful", "status": status_val}

@router.get("/{repo_id}/pulls")
def get_pending_pull_requests(repo_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    repo = db.query(Repository).filter(Repository.id == repo_id, Repository.owner_id == current_user.id).first()
    if not repo: raise HTTPException(status_code=403, detail="Not your repository")
    
    pending_files = db.query(File).filter(File.repo_id == repo.id, File.status == "PENDING_REVIEW").all()
    return[{"id": f.id, "filename": f.filename, "size": f.file_size, "uploader": f.uploader.username} for f in pending_files]

@router.post("/pulls/{file_id}/resolve")
def resolve_pull_request(file_id: str, action: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """ Action must be 'APPROVE' or 'REJECT' """
    file_record = db.query(File).filter(File.id == file_id, File.status == "PENDING_REVIEW").first()
    if not file_record: raise HTTPException(status_code=404)
    
    repo = file_record.repo
    if repo.owner_id != current_user.id: raise HTTPException(status_code=403)
    
    if action.upper() == "APPROVE":
        if current_user.storage_used + file_record.file_size > current_user.storage_limit:
            raise HTTPException(status_code=402, detail="Approving exceeds storage limit.")
        file_record.status = "APPROVED"
        current_user.storage_used += file_record.file_size
        db.commit()
        return {"message": "File approved and merged"}
        
    elif action.upper() == "REJECT":
        delete_from_s3(file_record.s3_key)
        db.delete(file_record)
        db.commit()
        return {"message": "Pull request rejected and file deleted"}

@router.delete("/{file_id}")
def delete_file(file_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    file_record = db.query(File).filter(File.id == file_id).first()
    if not file_record: raise HTTPException(status_code=404)
    
    repo = file_record.repo
    if not (repo.owner_id == current_user.id or file_record.uploader_id == current_user.id or current_user.role in ["ADMIN", "SUPERADMIN"]):
        raise HTTPException(status_code=403, detail="Forbidden")

    delete_from_s3(file_record.s3_key)
    if file_record.status == "APPROVED":
        repo.owner.storage_used = max(0, repo.owner.storage_used - file_record.file_size)

    db.delete(file_record)
    db.commit()
    return {"message": "File deleted"}