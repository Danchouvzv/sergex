from uuid import uuid4
from sqlalchemy import Column, String, ForeignKey, DateTime, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import enum

from app.db.session import Base


class FlightStatus(str, enum.Enum):
    """Enum for flight request status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FlightRequest(Base):
    """Flight request model with path geometry."""
    
    __tablename__ = "flight_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    drone_id = Column(UUID(as_uuid=True), ForeignKey("drones.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    altitude = Column(Float, nullable=False)
    # LINESTRING geometry for the flight path
    path = Column(Geometry("LINESTRING", srid=4326), nullable=False)
    status = Column(
        Enum(FlightStatus), 
        default=FlightStatus.PENDING, 
        nullable=False
    )
    rejection_reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    drone = relationship("Drone", back_populates="flight_requests")