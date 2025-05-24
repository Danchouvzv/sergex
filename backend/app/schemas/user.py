from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response schema."""
    id: UUID
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    """User update schema."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8) 