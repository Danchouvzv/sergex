from uuid import uuid4
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.db.session import Base


class NoFlyZone(Base):
    """No-fly zone model using PostGIS geometry types."""
    
    __tablename__ = "no_fly_zones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    # SRID 4326 is the WGS84 coordinate system used by GPS
    area = Column(Geometry("POLYGON", srid=4326), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 