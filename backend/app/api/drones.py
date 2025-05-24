from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.drone import Drone
from app.schemas.drone import DroneCreate, DroneResponse, DroneUpdate

router = APIRouter()


@router.get("/", response_model=List[DroneResponse])
def get_drones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get all drones for the current user."""
    if current_user.is_admin:
        # Админдар букил дронадарын коре алады
        drones = db.query(Drone).all()
    else:
        
        drones = db.query(Drone).filter(Drone.user_id == current_user.id).all()
    return drones


@router.post("/", response_model=DroneResponse, status_code=status.HTTP_201_CREATED)
def create_drone(
    drone_data: DroneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Create a new drone."""
    
    existing_drone = db.query(Drone).filter(Drone.serial_number == drone_data.serial_number).first()
    if existing_drone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Drone with this serial number already registered",
        )
    
    
    db_drone = Drone(
        model=drone_data.model,
        serial_number=drone_data.serial_number,
        user_id=current_user.id,
    )
    db.add(db_drone)
    db.commit()
    db.refresh(db_drone)
    return db_drone


@router.get("/{drone_id}", response_model=DroneResponse)
def get_drone(
    drone_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get a specific drone by ID."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found",
        )
    
    
    if not current_user.is_admin and drone.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return drone


@router.put("/{drone_id}", response_model=DroneResponse)
def update_drone(
    drone_id: UUID,
    drone_data: DroneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Update a drone."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found",
        )
    
    
    if not current_user.is_admin and drone.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    
    if drone_data.serial_number and drone_data.serial_number != drone.serial_number:
        existing_drone = db.query(Drone).filter(Drone.serial_number == drone_data.serial_number).first()
        if existing_drone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Drone with this serial number already exists",
            )
    
    
    if drone_data.model:
        drone.model = drone_data.model
    if drone_data.serial_number:
        drone.serial_number = drone_data.serial_number
    
    db.commit()
    db.refresh(drone)
    return drone


@router.delete("/{drone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_drone(
    drone_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a drone."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found",
        )
    
    
    if not current_user.is_admin and drone.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    db.delete(drone)
    db.commit()
    return None 