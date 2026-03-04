from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.ad import Ad
from app.schemas.ad import AdCreate, AdUpdate, AdResponse

router = APIRouter(tags=["Ads"])

@router.get("/ads/active", response_model=list[AdResponse])
async def get_active_ads(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ad).where(Ad.is_active == True).order_by(Ad.created_at.desc()))
    return result.scalars().all()

@router.get("/admin/ads", response_model=list[AdResponse])
async def list_all_ads(db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    result = await db.execute(select(Ad).order_by(Ad.created_at.desc()))
    return result.scalars().all()

@router.post("/admin/ads", response_model=AdResponse, status_code=201)
async def create_ad(data: AdCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    ad = Ad(**data.model_dump())
    db.add(ad)
    await db.flush()
    return ad

@router.put("/admin/ads/{ad_id}", response_model=AdResponse)
async def update_ad(ad_id: int, data: AdUpdate, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    result = await db.execute(select(Ad).where(Ad.id == ad_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(ad, k, v)
    return ad

@router.delete("/admin/ads/{ad_id}", status_code=204)
async def delete_ad(ad_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    result = await db.execute(select(Ad).where(Ad.id == ad_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    await db.delete(ad)

@router.post("/ads/{ad_id}/click")
async def track_click(ad_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ad).where(Ad.id == ad_id, Ad.is_active == True))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    ad.click_count += 1
    return {"target_url": ad.target_url}
