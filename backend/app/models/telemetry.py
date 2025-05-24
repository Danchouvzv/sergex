from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.db.session import Base


class DroneTelemetry(Base):
    """Drone telemetry model for position tracking."""
    
    __tablename__ = "drone_telemetry"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    drone_id = Column(UUID(as_uuid=True), ForeignKey("drones.id"), nullable=False)
    # Point geometry for drone position
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    altitude = Column(Float, nullable=False)
    speed = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)  # in degrees
    battery_level = Column(Float, nullable=True)  # percentage
    status = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    drone = relationship("Drone", back_populates="telemetry") 