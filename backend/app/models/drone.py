from uuid import uuid4
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Drone(Base):
    """Drone model."""
    
    __tablename__ = "drones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    model = Column(String, nullable=False)
    serial_number = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="drones")
    telemetry = relationship("DroneTelemetry", back_populates="drone", cascade="all, delete-orphan")
    flight_requests = relationship("FlightRequest", back_populates="drone", cascade="all, delete-orphan")
    violations = relationship("Violation", back_populates="drone", cascade="all, delete-orphan") 