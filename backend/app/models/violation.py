from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import enum

from app.db.session import Base


class ViolationType(str, enum.Enum):
    """Enum for violation types."""
    NO_FLY_ZONE = "no_fly_zone"
    OUT_OF_PATH = "out_of_path"
    ALTITUDE_VIOLATION = "altitude_violation"
    UNAUTHORIZED_FLIGHT = "unauthorized_flight"
    OTHER = "other"


class Violation(Base):
    """Violation model for tracking drone rule violations."""
    
    __tablename__ = "violations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    drone_id = Column(UUID(as_uuid=True), ForeignKey("drones.id"), nullable=False)
    flight_request_id = Column(UUID(as_uuid=True), ForeignKey("flight_requests.id"), nullable=True)
    type = Column(Enum(ViolationType), nullable=False)
    # Point geometry for violation location
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    drone = relationship("Drone", back_populates="violations")
    flight_request = relationship("FlightRequest") 