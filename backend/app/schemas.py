from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, conint, confloat, model_validator
from typing import Optional
from datetime import datetime
from .models import Category as CategoryEnum, EcoType as EcoTypeEnum, RequestStatus as RequestStatusEnum, AssignmentStatus as AssignmentStatusEnum

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class UserOut(BaseSchema):
    id: int
    max_user_id: str
    city_code: Optional[str] = None
    role_volunteer: bool
    role_requester: bool
    has_phone: bool  
    created_at: datetime

class RequestCreate(BaseSchema):
    max_user_id: str
    requester_id: Optional[int] = None
    category: CategoryEnum
    eco_type: Optional[EcoTypeEnum] = None
    vulnerable_group: Optional[str] = None
    title: str = Field(min_length=3, max_length=200)
    description: Optional[str] = None
    lat: confloat(ge=-90, le=90)  # type: ignore
    lon: confloat(ge=-180, le=180)  # type: ignore
    city_code: Optional[str] = None
    max_responses: Optional[conint(ge=1)] = None  # type: ignore
    donation_redirect_url: Optional[str] = None
    donation_phone: Optional[str] = None

class RequestOut(BaseSchema):
    id: int
    requester_id: int      
    max_user_id: Optional[str] = None
    category: CategoryEnum
    eco_type: Optional[EcoTypeEnum]
    vulnerable_group: Optional[str]
    title: str
    description: Optional[str]
    lat: float
    lon: float
    city_code: Optional[str]
    max_responses: Optional[int]
    status: RequestStatusEnum
    donation_redirect_url: Optional[str]
    donation_phone: Optional[str]
    created_at: datetime
    updated_at: datetime

class RequestFilters(BaseSchema):
    city_code: Optional[str] = None
    category: Optional[CategoryEnum] = None
    status: Optional[RequestStatusEnum] = RequestStatusEnum.open
    limit: int = 20
    offset: int = 0

class AssignmentCreate(BaseSchema):
    request_id: int
    volunteer_id: int

class AssignmentOut(BaseSchema):
    id: int
    request_id: int
    volunteer_id: int
    status: AssignmentStatusEnum
    accepted_at: Optional[datetime]
    confirmed_at: Optional[datetime]
    completed_at: Optional[datetime]

class BotUserUpsertIn(BaseSchema):
    max_user_id: str
    role: Optional[str] = None
    city_code: Optional[str] = None

class BotUserOut(BaseSchema):
    id: int
    max_user_id: str
    city_code: Optional[str]
    role_volunteer: bool
    role_requester: bool

class ApplyIn(BaseSchema):
    max_user_id: str  

class PhoneUpsertIn(BaseSchema):
    max_user_id: str
    phone_hash: str  # хранить хэш/маску

class ContactOut(BaseSchema):
    phone: str