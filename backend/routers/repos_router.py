# backend/routers/repos_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, Repository, File
from route.auth_router import get_current_user
from s3_utils import delete_from_s3

router = APIRouter(prefix="/api/repos", tags=["Repositories"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_repository(name: str, description: str = "", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if db.query(Repository).filter(Repository.owner_id == current_user.id, Repository.name == name).first():
        raise HTTPException(status_code=400, detail="Repository with this name already exists for your account.")
    
    repo = Repository(owner_id=current_user.id, name=name, description=description)
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return {"message": "Repository created", "repo": {"id": repo.id, "name": repo.name}}

@router.get("/")
def get_all_public_repos(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    # Everyone can see public repos
    repos = db.query(Repository).offset(skip).limit(limit).all()
    return[{"id": r.id, "name": r.name, "owner": r.owner.username, "verified": r.is_verified} for r in repos]

@router.get("/{username}/{repo_name}")
def get_repository_details(username: str, repo_name: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    repo = db.query(Repository).filter(Repository.owner_id == user.id, Repository.name == repo_name).first()
    if not repo: raise HTTPException(status_code=404, detail="Repository not found")
    
    # Get approved files for this repo
    files = db.query(File).filter(File.repo_id == repo.id, File.status == "APPROVED").all()
    
    return {
        "id": repo.id,
        "name": repo.name,
        "description": repo.description,
        "is_verified": repo.is_verified,
        "owner": user.username,
        "files":[{"id": f.id, "name": f.filename, "size": f.file_size, "is_raw": f.is_raw} for f in files]
    }

@router.delete("/{repo_id}")
def delete_repository(repo_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Deletes a repo. Verifies ownership or ADMIN rights.
    Deletes all files from S3, recalculates storage, updates user quota, and removes DB records.
    """
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo: raise HTTPException(status_code=404, detail="Repository not found")
    
    if repo.owner_id != current_user.id and current_user.role not in["ADMIN", "SUPERADMIN"]:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this repository")
    
    # 1. Fetch all files belonging to this repo
    files = db.query(File).filter(File.repo_id == repo.id).all()
    freed_space = 0
    
    # 2. Delete from ArvanCloud S3 & Calculate space to refund
    for file_record in files:
        delete_from_s3(file_record.s3_key)
        if file_record.status == "APPROVED":
            freed_space += file_record.file_size
            
    # 3. Refund space to the repository owner
    repo.owner.storage_used = max(0, repo.owner.storage_used - freed_space)
    
    # 4. Delete Database records (Files first, then Repo)
    db.query(File).filter(File.repo_id == repo.id).delete()
    db.delete(repo)
    db.commit()
    
    return {"message": f"Repository deleted. {freed_space / (1024*1024):.2f} MB of storage freed."}