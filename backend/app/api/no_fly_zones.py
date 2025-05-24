from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from shapely.geometry import shape
from geoalchemy2.shape import from_shape

from app.api.auth import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.no_fly_zone import NoFlyZone
from app.schemas.no_fly_zone import (
    NoFlyZoneCreate,
    NoFlyZoneResponse,
    NoFlyZoneUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[NoFlyZoneResponse])
def get_no_fly_zones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get all no-fly zones."""
    # All users can view no-fly zones
    zones = db.query(NoFlyZone).all()
    return zones


@router.post("/", response_model=NoFlyZoneResponse, status_code=status.HTTP_201_CREATED)
def create_no_fly_zone(
    zone_data: NoFlyZoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Create a new no-fly zone (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create no-fly zones",
        )
    
    # Convert GeoJSON to shapely geometry
    geom_shape = shape(zone_data.area)
    
    try:
        # Create no-fly zone
        no_fly_zone = NoFlyZone(
            name=zone_data.name,
            description=zone_data.description,
            area=from_shape(geom_shape, srid=4326),
            min_altitude=zone_data.min_altitude,
            max_altitude=zone_data.max_altitude,
            active=zone_data.active,
        )
        
        db.add(no_fly_zone)
        db.commit()
        db.refresh(no_fly_zone)
        
        return no_fly_zone
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A no-fly zone with this name already exists",
        )


@router.get("/{zone_id}", response_model=NoFlyZoneResponse)
def get_no_fly_zone(
    zone_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get a specific no-fly zone."""
    zone = db.query(NoFlyZone).filter(NoFlyZone.id == zone_id).first()
    
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No-fly zone not found",
        )
    
    return zone


@router.put("/{zone_id}", response_model=NoFlyZoneResponse)
def update_no_fly_zone(
    zone_id: UUID,
    zone_data: NoFlyZoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Update a no-fly zone (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update no-fly zones",
        )
    
    zone = db.query(NoFlyZone).filter(NoFlyZone.id == zone_id).first()
    
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No-fly zone not found",
        )
    
    # Update the fields if they're provided
    if zone_data.name is not None:
        zone.name = zone_data.name
    
    if zone_data.description is not None:
        zone.description = zone_data.description
    
    if zone_data.area is not None:
        geom_shape = shape(zone_data.area)
        zone.area = from_shape(geom_shape, srid=4326)
    
    if zone_data.min_altitude is not None:
        zone.min_altitude = zone_data.min_altitude
    
    if zone_data.max_altitude is not None:
        zone.max_altitude = zone_data.max_altitude
    
    if zone_data.active is not None:
        zone.active = zone_data.active
    
    try:
        db.commit()
        db.refresh(zone)
        return zone
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A no-fly zone with this name already exists",
        )


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_no_fly_zone(
    zone_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Delete a no-fly zone (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete no-fly zones",
        )
    
    zone = db.query(NoFlyZone).filter(NoFlyZone.id == zone_id).first()
    
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No-fly zone not found",
        )
    
    db.delete(zone)
    db.commit()
    
    return None 