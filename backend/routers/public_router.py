# backend/routers/public_router.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from models import User, Repository, File
from s3_utils import get_presigned_url

router = APIRouter(tags=["Public Raw Access"])

@router.get("/raw/{username}/{repo_name}/{filename}")
def get_raw_or_download_file(username: str, repo_name: str, filename: str, db: Session = Depends(get_db)):
    """ Redirects curl or browsers to the physical ArvanCloud file """
    user = db.query(User).filter(User.username == username).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    repo = db.query(Repository).filter(Repository.owner_id == user.id, Repository.name == repo_name).first()
    if not repo: raise HTTPException(status_code=404, detail="Repo not found")
    
    file_record = db.query(File).filter(File.repo_id == repo.id, File.filename == filename, File.status == "APPROVED").first()
    if not file_record: raise HTTPException(status_code=404, detail="File not found")

    url = get_presigned_url(file_record.s3_key, is_raw=file_record.is_raw)
    return RedirectResponse(url=url)