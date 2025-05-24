from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class DroneBase(BaseModel):
    """Base drone schema."""
    model: str
    serial_number: str


class DroneCreate(DroneBase):
    """Drone creation schema."""
    pass


class DroneResponse(DroneBase):
    """Drone response schema."""
    id: UUID
    user_id: UUID
    created_at: datetime
    
    class Config:
        orm_mode = True


class DroneUpdate(BaseModel):
    """Drone update schema."""
    model: Optional[str] = None
    serial_number: Optional[str] = None


class DroneWithUser(DroneResponse):
    """Drone with user information schema."""
    user_name: str 