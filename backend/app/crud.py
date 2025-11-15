from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence, Optional
from .models import User, Request, Assignment, RequestStatus, AssignmentStatus
from .schemas import RequestCreate, RequestFilters, AssignmentCreate
from .models import Category as CategoryEnum, EcoType as EcoTypeEnum  


async def get_or_create_user(db: AsyncSession, max_user_id: str, city_code: Optional[str] = None) -> User:
    q = await db.execute(select(User).where(User.max_user_id == max_user_id))
    u = q.scalar_one_or_none()
    if u:
        return u
    u = User(max_user_id=max_user_id, city_code=city_code, role_requester=True, role_volunteer=True)
    db.add(u)
    await db.flush()
    return u

async def create_request(db: AsyncSession, data: RequestCreate) -> Request:
    cat = CategoryEnum(data.category) if isinstance(data.category, str) else data.category
    eco = (EcoTypeEnum(data.eco_type) if isinstance(data.eco_type, str) else data.eco_type)

    r = Request(
        requester_id=data.requester_id,
        category=cat,
        eco_type=eco,
        vulnerable_group=data.vulnerable_group,
        title=data.title,
        description=data.description,
        lat=data.lat,
        lon=data.lon,
        city_code=data.city_code,
        max_responses=data.max_responses,
    )
    db.add(r)
    await db.flush()
    return r

async def list_requests(db: AsyncSession, f: RequestFilters) -> Sequence[Request]:
    stmt = select(Request)
    if f.city_code:
        stmt = stmt.where(Request.city_code == f.city_code)
    if f.category:
        stmt = stmt.where(Request.category == CategoryEnum(f.category))
    if f.status:
        stmt = stmt.where(Request.status == f.status)  # open by default
    stmt = stmt.order_by(Request.created_at.desc()).limit(f.limit).offset(f.offset)
    res = await db.execute(stmt)
    return res.scalars().all()

async def get_request(db: AsyncSession, request_id: int) -> Optional[Request]:
    res = await db.execute(select(Request).where(Request.id == request_id))
    return res.scalar_one_or_none()

async def create_assignment(db: AsyncSession, data: AssignmentCreate) -> Assignment:
    a = Assignment(request_id=data.request_id, volunteer_id=data.volunteer_id)
    db.add(a)
    await db.flush()
    return a

async def update_assignment_status(db: AsyncSession, assignment_id: int, status: AssignmentStatus) -> Optional[Assignment]:
    res = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    a = res.scalar_one_or_none()
    if not a:
        return None
    a.status = status
    await db.flush()
    return a

async def upsert_user_profile(
    db: AsyncSession,
    max_user_id: str,
    role: Optional[str],
    city_code: Optional[str],
) -> User:
    q = await db.execute(select(User).where(User.max_user_id == max_user_id))
    u = q.scalar_one_or_none()
    if not u:
        u = User(
            max_user_id=max_user_id,
            role_requester=True, 
            role_volunteer=True,
            city_code=city_code
        )
        db.add(u)
        await db.flush()
    else:
        if city_code is not None:
            u.city_code = city_code

    if role:
        r = role.lower().strip()
        if r in ("volunteer", "волонтёр", "волонтер"):
            u.role_volunteer = True
            u.role_requester = u.role_requester or False
        elif r in ("requester", "нуждающийся", "заявитель", "прошу помощь"):
            u.role_requester = True
            u.role_volunteer = u.role_volunteer or False

    await db.flush()
    return u

async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    res = await db.execute(select(User).where(User.id == user_id))
    return res.scalar_one_or_none()

async def get_user_by_max_user_id(db: AsyncSession, max_user_id: str) -> Optional[User]:
    res = await db.execute(select(User).where(User.max_user_id == str(max_user_id)))
    return res.scalar_one_or_none()

async def get_assignment_by_pair(db: AsyncSession, request_id: int, volunteer_id: int) -> Optional[Assignment]:
    res = await db.execute(select(Assignment).where(
        Assignment.request_id == request_id, Assignment.volunteer_id == volunteer_id
    ))
    return res.scalar_one_or_none()

async def list_assignments_by_request(db: AsyncSession, request_id: int) -> Sequence[Assignment]:
    res = await db.execute(select(Assignment).where(Assignment.request_id == request_id))
    return res.scalars().all()