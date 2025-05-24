from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.api.auth import get_current_active_user, get_user_from_token
from app.db.session import get_db
from app.models.user import User
from app.models.drone import Drone
from app.models.telemetry import Telemetry
from app.models.no_fly_zone import NoFlyZone
from app.models.violation import Violation, ViolationType
from app.schemas.telemetry import TelemetryCreate, TelemetryResponse

router = APIRouter()


@router.get("/drone/{drone_id}", response_model=List[TelemetryResponse])
def get_drone_telemetry(
    drone_id: UUID,
    limit: int = 100,
    start_time: datetime = None,
    end_time: datetime = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get telemetry data for a specific drone."""
    
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
    
    
    query = db.query(Telemetry).filter(Telemetry.drone_id == drone_id)
    
    
    if start_time:
        query = query.filter(Telemetry.timestamp >= start_time)
    
    if end_time:
        query = query.filter(Telemetry.timestamp <= end_time)
    
    
    telemetry_data = query.order_by(Telemetry.timestamp.desc()).limit(limit).all()
    
    
    telemetry_data.reverse()
    
    return telemetry_data


@router.get("/latest/{drone_id}", response_model=TelemetryResponse)
def get_latest_telemetry(
    drone_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get the latest telemetry data for a specific drone."""
    
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
    
    
    latest_telemetry = db.query(Telemetry).filter(
        Telemetry.drone_id == drone_id
    ).order_by(Telemetry.timestamp.desc()).first()
    
    if not latest_telemetry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No telemetry data found for this drone",
        )
    
    return latest_telemetry


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_telemetry(
    telemetry_data: TelemetryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Create new telemetry data entry (for testing only)."""
    
    drone = db.query(Drone).filter(Drone.id == telemetry_data.drone_id).first()
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
    
    
    point = Point(telemetry_data.longitude, telemetry_data.latitude)
    
    
    telemetry = Telemetry(
        drone_id=telemetry_data.drone_id,
        timestamp=telemetry_data.timestamp or datetime.utcnow(),
        latitude=telemetry_data.latitude,
        longitude=telemetry_data.longitude,
        altitude=telemetry_data.altitude,
        speed=telemetry_data.speed,
        heading=telemetry_data.heading,
        battery_level=telemetry_data.battery_level,
        position=from_shape(point, srid=4326)
    )
    
    db.add(telemetry)
    db.commit()
    
    
    check_for_violations(db, telemetry)
    
    return {"message": "Telemetry data received"}



@router.websocket("/ws/{drone_id}")
async def websocket_telemetry(
    websocket: WebSocket,
    drone_id: str,
    token: str,
    db: Session = Depends(get_db),
):
    """WebSocket connection for real-time telemetry updates."""
    
    try:
        user = get_user_from_token(token, db)
        if not user:
            await websocket.close(code=1008) 
            return
        
        
        drone = db.query(Drone).filter(Drone.id == drone_id).first()
        if not drone:
            await websocket.close(code=1008)
            return
        
        if not user.is_admin and drone.user_id != user.id:
            await websocket.close(code=1008)
            return
        
        await websocket.accept()
        
        
        try:
            while True:
                data = await websocket.receive_json()
                
                
                if "latitude" in data and "longitude" in data:
                    point = Point(data["longitude"], data["latitude"])
                    
                    
                    telemetry = Telemetry(
                        drone_id=drone_id,
                        timestamp=datetime.utcnow(),
                        latitude=data["latitude"],
                        longitude=data["longitude"],
                        altitude=data.get("altitude", 0),
                        speed=data.get("speed", 0),
                        heading=data.get("heading", 0),
                        battery_level=data.get("battery_level", 100),
                        position=from_shape(point, srid=4326)
                    )
                    
                    db.add(telemetry)
                    db.commit()
                    db.refresh(telemetry)
                    
                    
                    violations = check_for_violations(db, telemetry)
                    
                    
                    await websocket.send_json({
                        "status": "ok",
                        "violations": violations
                    })
                else:
                    await websocket.send_json({
                        "status": "error",
                        "message": "Invalid telemetry data"
                    })
                    
        except WebSocketDisconnect:
            
            pass
            
    except Exception as e:
        
        try:
            await websocket.close(code=1011) 
        except:
            pass


def check_for_violations(db: Session, telemetry: Telemetry) -> List[dict]:
    """Check if telemetry data violates any no-fly zones."""
    violations = []
    
    
    no_fly_zones = db.query(NoFlyZone).filter(NoFlyZone.active == True).all()
    
    for zone in no_fly_zones:
        
        if db.query(
            zone.area.ST_Contains(telemetry.position)
        ).scalar():
            
            altitude_violation = False
            if (zone.min_altitude is not None and telemetry.altitude < zone.min_altitude) or \
               (zone.max_altitude is not None and telemetry.altitude > zone.max_altitude):
                altitude_violation = True
            
            
            violation = Violation(
                drone_id=telemetry.drone_id,
                no_fly_zone_id=zone.id,
                timestamp=telemetry.timestamp,
                position=telemetry.position,
                type=ViolationType.NO_FLY_ZONE,
                description=f"Drone entered no-fly zone: {zone.name}" + 
                            (f" (altitude violation: {telemetry.altitude}m)" if altitude_violation else "")
            )
            
            db.add(violation)
            db.commit()
            
            violations.append({
                "zone_id": str(zone.id),
                "zone_name": zone.name,
                "type": "NO_FLY_ZONE",
                "description": violation.description
            })
    
    
    
    return violations 