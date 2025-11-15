from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import Enum as SAEnum
import enum
from datetime import datetime

Base = declarative_base()

class RequestStatus(str, enum.Enum):
    open = "open"; in_progress = "in_progress"; done = "done"; cancelled = "cancelled"

class Category(str, enum.Enum):
    social = "social"; eco = "eco"

class EcoType(str, enum.Enum):
    cleanup = "cleanup"; recycling = "recycling"; tree_planting = "tree_planting"

class AssignmentStatus(str, enum.Enum):
    applied = "applied"; accepted = "accepted"; confirmed = "confirmed"; completed = "completed"; cancelled = "cancelled"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    max_user_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    phone_hash: Mapped[str | None] = mapped_column(String(128))
    role_volunteer: Mapped[bool] = mapped_column(default=True)
    role_requester: Mapped[bool] = mapped_column(default=True)
    city_code: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

class Request(Base):
    __tablename__ = "requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category: Mapped[Category] = mapped_column(
        SAEnum(Category, name="category", native_enum=False, validate_strings=True)
    )
    eco_type: Mapped[EcoType | None] = mapped_column(
        SAEnum(EcoType, name="eco_type", native_enum=False, validate_strings=True),
        nullable=True
    )
    vulnerable_group: Mapped[str | None] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    city_code: Mapped[str | None] = mapped_column(String(64), index=True)
    max_responses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[RequestStatus] = mapped_column(
        SAEnum(RequestStatus, name="request_status", native_enum=False, validate_strings=True),
        default=RequestStatus.open,
        index=True
    )
    donation_redirect_url: Mapped[str | None] = mapped_column(String(500))
    donation_phone: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), index=True)
    volunteer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[AssignmentStatus] = mapped_column(
        SAEnum(AssignmentStatus, name="assignment_status", native_enum=False, validate_strings=True),
        default=AssignmentStatus.applied,
        index=True
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
