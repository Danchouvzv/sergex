from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from shapely.geometry import shape
from geoalchemy2.shape import from_shape

from app.api.auth import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.drone import Drone
from app.models.flight_request import FlightRequest, FlightStatus
from app.models.no_fly_zone import NoFlyZone
from app.schemas.flight_request import (
    FlightRequestCreate,
    FlightRequestResponse,
    FlightRequestUpdate,
    FlightRequestCheck,
)

router = APIRouter()


@router.post("/check-route", status_code=status.HTTP_200_OK)
def check_flight_route(
    route_data: FlightRequestCheck,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Check if a flight route intersects with no-fly zones."""
    # Convert GeoJSON to shapely geometry
    route_shape = shape(route_data.path)
    
    # Get all no-fly zones
    no_fly_zones = db.query(NoFlyZone).all()
    
    # Check for intersections
    violations = []
    for zone in no_fly_zones:
        zone_shape = zone.area.data
        if route_shape.intersects(zone_shape):
            violations.append({
                "zone_id": str(zone.id),
                "zone_name": zone.name,
                "description": zone.description,
            })
    
    return {
        "is_valid": len(violations) == 0,
        "violations": violations,
    }


@router.get("/", response_model=List[FlightRequestResponse])
def get_flight_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get all flight requests for the current user's drones."""
    if current_user.is_admin:
        # Admins can see all flight requests
        flight_requests = db.query(FlightRequest).all()
    else:
        # Regular users only see their own drones' flight requests
        flight_requests = (
            db.query(FlightRequest)
            .join(Drone, FlightRequest.drone_id == Drone.id)
            .filter(Drone.user_id == current_user.id)
            .all()
        )
    return flight_requests


@router.get("/active", response_model=List[FlightRequestResponse])
def get_active_flight_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get active flight requests (approved or in progress)."""
    active_statuses = [FlightStatus.APPROVED, FlightStatus.IN_PROGRESS]
    
    if current_user.is_admin:
        # Admins can see all active flight requests
        flight_requests = db.query(FlightRequest).filter(FlightRequest.status.in_(active_statuses)).all()
    else:
        # Regular users only see their own drones' active flight requests
        flight_requests = (
            db.query(FlightRequest)
            .join(Drone, FlightRequest.drone_id == Drone.id)
            .filter(Drone.user_id == current_user.id, FlightRequest.status.in_(active_statuses))
            .all()
        )
    return flight_requests


@router.post("/", response_model=FlightRequestResponse, status_code=status.HTTP_201_CREATED)
def create_flight_request(
    flight_data: FlightRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Create a new flight request."""
    # Check if the drone exists and belongs to the user
    drone = db.query(Drone).filter(Drone.id == flight_data.drone_id).first()
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found",
        )
    
    if not current_user.is_admin and drone.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to use this drone",
        )
    
    # Convert GeoJSON to shapely geometry
    route_shape = shape(flight_data.path)
    
    # Get all no-fly zones
    no_fly_zones = db.query(NoFlyZone).all()
    
    # Check for intersections
    status = FlightStatus.PENDING
    rejection_reason = None
    
    for zone in no_fly_zones:
        zone_shape = zone.area.data
        if route_shape.intersects(zone_shape):
            status = FlightStatus.REJECTED
            rejection_reason = f"Flight path intersects with no-fly zone: {zone.name}"
            break
    
    # Create flight request
    flight_request = FlightRequest(
        drone_id=flight_data.drone_id,
        start_time=flight_data.start_time,
        end_time=flight_data.end_time,
        altitude=flight_data.altitude,
        path=from_shape(route_shape, srid=4326),
        status=status,
        rejection_reason=rejection_reason,
    )
    
    db.add(flight_request)
    db.commit()
    db.refresh(flight_request)
    
    return flight_request


@router.get("/{flight_id}", response_model=FlightRequestResponse)
def get_flight_request(
    flight_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get a specific flight request."""
    flight_request = db.query(FlightRequest).filter(FlightRequest.id == flight_id).first()
    
    if not flight_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight request not found",
        )
    
    # Check if the user has access to this flight request
    if not current_user.is_admin:
        drone = db.query(Drone).filter(Drone.id == flight_request.drone_id).first()
        if drone.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    
    return flight_request


@router.put("/{flight_id}", response_model=FlightRequestResponse)
def update_flight_request(
    flight_id: UUID,
    flight_data: FlightRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Update a flight request (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update flight requests",
        )
    
    flight_request = db.query(FlightRequest).filter(FlightRequest.id == flight_id).first()
    
    if not flight_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight request not found",
        )
    
    # Update flight request
    if flight_data.status is not None:
        flight_request.status = flight_data.status
    
    if flight_data.rejection_reason is not None:
        flight_request.rejection_reason = flight_data.rejection_reason
    
    db.commit()
    db.refresh(flight_request)
    
    return flight_request 