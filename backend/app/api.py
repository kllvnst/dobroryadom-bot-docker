from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from .models import Assignment
from .db import get_db
from . import crud
from .schemas import (
    ContactOut, RequestCreate, RequestOut, RequestFilters,
    AssignmentCreate, AssignmentOut
)
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from .schemas import ApplyIn, AssignmentOut, PhoneUpsertIn, AssignmentStatusEnum
from sqlalchemy import select

router = APIRouter(prefix="/api/v1", tags=["api"])

@router.post("/requests", response_model=RequestOut)
async def create_request(data: RequestCreate, db: AsyncSession = Depends(get_db)):
    if not data.max_user_id:
        raise HTTPException(status_code=400, detail="max_user_id is required")
    try:
        # создаём/получаем пользователя по max_user_id
        user = await crud.get_or_create_user(db, max_user_id=str(data.max_user_id), city_code=data.city_code)
        data_fixed = data.model_copy(update={"requester_id": user.id})
        req = await crud.create_request(db, data_fixed)
        await db.commit()
        await db.refresh(req)
        return req
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"create_request failed: {e}")

@router.get("/requests", response_model=List[RequestOut])
async def list_requests(city_code: str | None = None,
                        category: str | None = None,
                        status: str | None = "open",
                        limit: int = 20, offset: int = 0,
                        db: AsyncSession = Depends(get_db)):
    f = RequestFilters(city_code=city_code, category=category, status=status, limit=limit, offset=offset)
    items = await crud.list_requests(db, f)
    return items

@router.post("/requests/{request_id}/apply", response_model=AssignmentOut)
async def apply_request(
    request_id: int = Path(..., ge=1),
    data: ApplyIn = Body(...),
    db: AsyncSession = Depends(get_db),
):
    req = await crud.get_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="request not found")

    vol = await crud.get_user_by_max_user_id(db, data.max_user_id)
    if not vol:
        vol = await crud.get_or_create_user(db, data.max_user_id)

    existing = await crud.get_assignment_by_pair(db, request_id, vol.id)
    if existing:
        return existing  

    a = await crud.create_assignment(db, data=crud.AssignmentCreate(request_id=request_id, volunteer_id=vol.id))
    await db.commit()
    await db.refresh(a)
    return a

@router.get("/requests/{request_id}/applicants", response_model=list[AssignmentOut])
async def list_applicants(
    request_id: int = Path(..., ge=1),
    requester_max_user_id: str = "",
    db: AsyncSession = Depends(get_db),
):
    req = await crud.get_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="request not found")

    owner = await crud.get_user_by_id(db, req.requester_id)
    if not owner or (requester_max_user_id and owner.max_user_id != requester_max_user_id):
        raise HTTPException(status_code=403, detail="forbidden")

    items = await crud.list_assignments_by_request(db, request_id)
    return items

@router.post("/assignments", response_model=AssignmentOut)
async def apply_for_request(data: AssignmentCreate, db: AsyncSession = Depends(get_db)):
    a = await crud.create_assignment(db, data)
    await db.commit()
    await db.refresh(a)
    return a

@router.patch("/assignments/{assignment_id}/status", response_model=AssignmentOut)
async def update_assignment(
    assignment_id: int = Path(..., ge=1),
    status: AssignmentStatusEnum = Body(..., embed=True),
    requester_max_user_id: str = Body("", embed=True),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(crud.Assignment).where(crud.Assignment.id == assignment_id))
    a = res.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="assignment not found")

    req = await crud.get_request(db, a.request_id)
    owner = await crud.get_user_by_id(db, req.requester_id) if req else None
    if not req or not owner or (requester_max_user_id and owner.max_user_id != requester_max_user_id):
        raise HTTPException(status_code=403, detail="forbidden")

    a = await crud.update_assignment_status(db, assignment_id, status)
    await db.commit(); 
    await db.refresh(a)
    return a

ALLOWED_TO_SHOW = {"accepted", "confirmed", "completed"}
@router.get("/assignments/{assignment_id}/contact", response_model=ContactOut)
async def get_assignment_contact(
    assignment_id: int = Path(..., ge=1),
    requester_max_user_id: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    a = res.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="assignment not found")

    req = await crud.get_request(db, a.request_id)
    if not req:
        raise HTTPException(status_code=404, detail="request not found")
    owner = await crud.get_user_by_id(db, req.requester_id)
    if not owner or (requester_max_user_id and owner.max_user_id != requester_max_user_id):
        raise HTTPException(status_code=403, detail="forbidden")

    if a.status not in ALLOWED_TO_SHOW:
        raise HTTPException(status_code=403, detail="not accepted yet")

    vol = await crud.get_user_by_id(db, a.volunteer_id)
    if not vol or not vol.phone_hash:
        raise HTTPException(status_code=404, detail="phone not set")

    return ContactOut(phone=vol.phone_hash)