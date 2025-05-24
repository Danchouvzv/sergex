from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, validator
from geojson import LineString

from app.models.flight_request import FlightStatus


class FlightRequestBase(BaseModel):
    """Base flight request schema."""
    drone_id: UUID
    start_time: datetime
    end_time: datetime
    altitude: float


class FlightRequestCreate(FlightRequestBase):
    """Flight request creation schema."""
    
    path: LineString
    
    @validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class FlightRequestResponse(FlightRequestBase):
    """Flight request response schema."""
    id: UUID
    path: LineString
    status: FlightStatus
    rejection_reason: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


class FlightRequestUpdate(BaseModel):
    """Flight request update schema."""
    status: Optional[FlightStatus] = None
    rejection_reason: Optional[str] = None


class FlightRequestCheck(BaseModel):
    """Flight request check schema."""
    path: LineString
    altitude: float 