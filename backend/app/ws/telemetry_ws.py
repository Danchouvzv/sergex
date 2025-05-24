from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, List, Any
import json
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.drone import Drone
from app.api.auth import get_user_from_token

router = APIRouter()

# Store active connections
active_connections: Dict[str, List[WebSocket]] = {}


@router.websocket("/ws/telemetry")
async def telemetry_websocket(
    websocket: WebSocket,
    token: str = None,
    db: Session = Depends(get_db),
):
    """WebSocket endpoint for real-time telemetry updates."""
    # Authenticate the user
    user = None
    if token:
        user = get_user_from_token(token, db)
    
    if not user:
        await websocket.close(code=1008)  # Policy Violation
        return
    
    await websocket.accept()
    
    # Register to receive telemetry updates for all drones the user has access to
    drones = []
    if user.is_admin:
        # Admins can see all drones
        drones = db.query(Drone).all()
    else:
        # Regular users can only see their drones
        drones = db.query(Drone).filter(Drone.user_id == user.id).all()
    
    # Create list of drone IDs
    drone_ids = [str(drone.id) for drone in drones]
    
    # Add connection to active connections for each drone
    for drone_id in drone_ids:
        if drone_id not in active_connections:
            active_connections[drone_id] = []
        active_connections[drone_id].append(websocket)
    
    try:
        # Keep the connection alive
        while True:
            # Wait for messages (ping/pong for keep-alive)
            data = await websocket.receive_text()
            
            # Process commands if needed
            if data.startswith('{"command":'):
                try:
                    command_data = json.loads(data)
                    command = command_data.get("command")
                    
                    if command == "ping":
                        await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                except Exception:
                    pass
            
    except WebSocketDisconnect:
        # Remove connection from active connections
        for drone_id in drone_ids:
            if drone_id in active_connections:
                active_connections[drone_id].remove(websocket)
                if not active_connections[drone_id]:
                    del active_connections[drone_id]


async def broadcast_telemetry(drone_id: str, telemetry_data: dict):
    """Broadcast telemetry data to all connected clients for a specific drone."""
    if drone_id in active_connections:
        disconnected_websockets = []
        
        for websocket in active_connections[drone_id]:
            try:
                await websocket.send_json({
                    "type": "telemetry",
                    "drone_id": drone_id,
                    "data": telemetry_data,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception:
                disconnected_websockets.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            active_connections[drone_id].remove(websocket)
            
        if not active_connections[drone_id]:
            del active_connections[drone_id]


async def broadcast_violation(drone_id: str, violation_data: dict):
    """Broadcast violation data to all connected clients for a specific drone."""
    if drone_id in active_connections:
        disconnected_websockets = []
        
        for websocket in active_connections[drone_id]:
            try:
                await websocket.send_json({
                    "type": "violation",
                    "drone_id": drone_id,
                    "data": violation_data,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception:
                disconnected_websockets.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            active_connections[drone_id].remove(websocket)
            
        if not active_connections[drone_id]:
            del active_connections[drone_id] 