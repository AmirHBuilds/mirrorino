# backend/routers/admin_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Repository, File
from route.auth_router import get_current_admin
from s3_utils import delete_from_s3

router = APIRouter(prefix="/api/admin", tags=["Admin"], dependencies=[Depends(get_current_admin)])

@router.get("/stats")
def get_system_stats(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_repos = db.query(Repository).count()
    total_files = db.query(File).count()
    
    # Calculate total storage used across all users
    users = db.query(User).all()
    total_storage_bytes = sum(u.storage_used for u in users)
    
    return {
        "total_users": total_users,
        "total_repos": total_repos,
        "total_files": total_files,
        "total_storage_mb": round(total_storage_bytes / (1024*1024), 2)
    }

@router.put("/users/{username}/quota")
def update_user_quota(username: str, limit_mb: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user: raise HTTPException(status_code=404)
    user.storage_limit = limit_mb * 1024 * 1024
    db.commit()
    return {"message": f"Quota updated to {limit_mb}MB"}

@router.put("/users/{username}/ban")
def toggle_user_ban(username: str, ban: bool, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user: raise HTTPException(status_code=404)
    user.is_banned = ban
    db.commit()
    return {"message": f"User {'banned' if ban else 'unbanned'}"}

@router.put("/repos/{repo_id}/verify")
def verify_repo(repo_id: str, verify: bool, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo: raise HTTPException(status_code=404)
    
    repo.is_verified = verify
    if verify:
        # Auto-upgrade owner to 2GB limit if verified
        repo.owner.storage_limit = max(repo.owner.storage_limit, 2048 * 1024 * 1024)
    db.commit()
    return {"message": "Repo verification updated"}

@router.delete("/users/{username}")
def delete_user_and_everything(username: str, db: Session = Depends(get_db)):
    """ DANGEROUS: Wipes a user, all their repos, and all files from S3. """
    user = db.query(User).filter(User.username == username).first()
    if not user: raise HTTPException(status_code=404)
    if user.role == "SUPERADMIN": raise HTTPException(status_code=403, detail="Cannot delete superadmin")
    
    repos = db.query(Repository).filter(Repository.owner_id == user.id).all()
    for repo in repos:
        # Delete files from S3
        files = db.query(File).filter(File.repo_id == repo.id).all()
        for f in files: delete_from_s3(f.s3_key)
        # Delete files from DB
        db.query(File).filter(File.repo_id == repo.id).delete()
    
    # Delete Repos DB records
    db.query(Repository).filter(Repository.owner_id == user.id).delete()
    # Delete User
    db.delete(user)
    db.commit()
    return {"message": "User and all associated data completely wiped."}