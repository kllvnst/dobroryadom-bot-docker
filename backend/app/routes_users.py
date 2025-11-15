from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .db import get_db
from . import crud
from .schemas import BotUserUpsertIn, BotUserOut, PhoneUpsertIn

router = APIRouter(prefix="/api/v1/bot/users", tags=["bot-users"])

@router.get("/{max_user_id}", response_model=BotUserOut)
async def get_user(max_user_id: str, db: AsyncSession = Depends(get_db)):
    u = await crud.get_user_by_max_user_id(db, max_user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    out = BotUserOut.model_validate(u).model_dump()
    out["has_phone"] = bool(u.phone_hash)  # NEW
    return out

@router.get("/by-id/{user_id}", response_model=BotUserOut)
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    u = await crud.get_user_by_id(db, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    out = BotUserOut.model_validate(u).model_dump()
    out["has_phone"] = bool(u.phone_hash)
    return out


@router.put("", response_model=BotUserOut)
async def upsert_user(payload: BotUserUpsertIn, db: AsyncSession = Depends(get_db)):
    u = await crud.upsert_user_profile(db, payload.max_user_id, payload.role, payload.city_code)
    await db.commit()
    await db.refresh(u)
    return u

@router.put("/phone")
async def upsert_phone(data: PhoneUpsertIn, db: AsyncSession = Depends(get_db)):
    u = await crud.get_user_by_max_user_id(db, data.max_user_id)  # <-- тоже по max_user_id
    if not u:
        u = await crud.get_or_create_user(db, data.max_user_id)
    u.phone_hash = data.phone_hash
    await db.commit()
    return {"ok": True}