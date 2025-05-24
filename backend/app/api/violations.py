from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.api.auth import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.drone import Drone
from app.models.violation import Violation
from app.schemas.violation import ViolationResponse

router = APIRouter()


@router.get("/", response_model=List[ViolationResponse])
def get_violations(
    drone_id: UUID = None,
    start_time: datetime = None,
    end_time: datetime = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get all violations, optionally filtered by drone and time range."""
    # Build the base query
    query = db.query(Violation)
    
    # Filter by drone if specified
    if drone_id:
        query = query.filter(Violation.drone_id == drone_id)
        
        # Check if the user has access to this drone
        if not current_user.is_admin:
            drone = db.query(Drone).filter(Drone.id == drone_id).first()
            if not drone or drone.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions",
                )
    else:
        # If no specific drone is requested, filter by user's drones
        if not current_user.is_admin:
            query = query.join(Drone, Violation.drone_id == Drone.id).filter(Drone.user_id == current_user.id)
    
    # Apply time filters if provided
    if start_time:
        query = query.filter(Violation.timestamp >= start_time)
    
    if end_time:
        query = query.filter(Violation.timestamp <= end_time)
    
    # Get the violations, limited by the limit parameter
    violations = query.order_by(Violation.timestamp.desc()).limit(limit).all()
    
    return violations


@router.get("/recent", response_model=List[ViolationResponse])
def get_recent_violations(
    hours: int = 24,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get recent violations within the specified time window."""
    # Calculate the start time
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Build the base query
    query = db.query(Violation).filter(Violation.timestamp >= start_time)
    
    # Filter by user's drones if not admin
    if not current_user.is_admin:
        query = query.join(Drone, Violation.drone_id == Drone.id).filter(Drone.user_id == current_user.id)
    
    # Get the violations, limited by the limit parameter
    violations = query.order_by(Violation.timestamp.desc()).limit(limit).all()
    
    return violations


@router.get("/drone/{drone_id}", response_model=List[ViolationResponse])
def get_drone_violations(
    drone_id: UUID,
    start_time: datetime = None,
    end_time: datetime = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get violations for a specific drone."""
    # Check if the drone exists
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found",
        )
    
    # Check if the user has access to this drone
    if not current_user.is_admin and drone.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Build the query
    query = db.query(Violation).filter(Violation.drone_id == drone_id)
    
    # Apply time filters if provided
    if start_time:
        query = query.filter(Violation.timestamp >= start_time)
    
    if end_time:
        query = query.filter(Violation.timestamp <= end_time)
    
    # Get the violations, limited by the limit parameter
    violations = query.order_by(Violation.timestamp.desc()).limit(limit).all()
    
    return violations


@router.get("/{violation_id}", response_model=ViolationResponse)
def get_violation(
    violation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get a specific violation."""
    violation = db.query(Violation).filter(Violation.id == violation_id).first()
    
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Violation not found",
        )
    
    # Check if the user has access to this violation
    if not current_user.is_admin:
        drone = db.query(Drone).filter(Drone.id == violation.drone_id).first()
        if drone.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    
    return violation 