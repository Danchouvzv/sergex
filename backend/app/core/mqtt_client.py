import json
import logging
from typing import Callable, Dict, Any, Optional
import asyncio

import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.telemetry import DroneTelemetry
from app.models.drone import Drone
from app.models.flight_request import FlightRequest, FlightStatus
from app.models.violation import Violation, ViolationType
from app.ws.telemetry_ws import broadcast_telemetry
from geoalchemy2.shape import from_shape
from shapely.geometry import Point, LineString, mapping
import shapely.wkb

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT client for processing telemetry data."""
    
    def __init__(self):
        """Initialize MQTT client."""
        self.client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
    
    def connect(self):
        """Connect to MQTT broker."""
        self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
        logger.info(f"Connected to MQTT broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        logger.info(f"Connected with result code {rc}")
        
        client.subscribe(settings.MQTT_TELEMETRY_TOPIC)
        logger.info(f"Subscribed to {settings.MQTT_TELEMETRY_TOPIC}")
    
    def on_message(self, client, userdata, msg):
        """Callback for when a message is received from the broker."""
        try:
            
            payload = json.loads(msg.payload.decode())
            logger.debug(f"Received message: {payload}")
            
            
            asyncio.run(self.process_telemetry(payload))
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def process_telemetry(self, telemetry: Dict[str, Any]):
        """Process and store telemetry data."""
        db = SessionLocal()
        try:
            
            drone_id = telemetry.get("drone_id")
            if not drone_id:
                logger.error("Telemetry missing drone_id")
                return
            
            
            drone = db.query(Drone).filter(Drone.id == drone_id).first()
            if not drone:
                logger.error(f"Drone with ID {drone_id} not found")
                return
            
            
            location_data = telemetry.get("location", {})
            coordinates = location_data.get("coordinates", [])
            if not coordinates or len(coordinates) < 2:
                logger.error("Invalid location coordinates")
                return
            
            
            point = Point(coordinates[0], coordinates[1])
            wkb_point = from_shape(point, srid=4326)
            
            
            db_telemetry = DroneTelemetry(
                drone_id=drone_id,
                location=wkb_point,
                altitude=telemetry.get("altitude", 0.0),
                speed=telemetry.get("speed"),
                heading=telemetry.get("heading"),
                battery_level=telemetry.get("battery_level"),
                status=telemetry.get("status"),
            )
            db.add(db_telemetry)
            
            
            flight_request = (
                db.query(FlightRequest)
                .filter(
                    FlightRequest.drone_id == drone_id,
                    FlightRequest.status.in_([FlightStatus.APPROVED, FlightStatus.IN_PROGRESS]),
                )
                .order_by(FlightRequest.start_time.desc())
                .first()
            )
            
            
            violations = []
            if flight_request:
                
                path = flight_request.path
                path_shape = shapely.wkb.loads(bytes(path.data))
                
                
                buffer_distance = 0.001 
                if not path_shape.buffer(buffer_distance).contains(point):
                    
                    violation = Violation(
                        drone_id=drone_id,
                        flight_request_id=flight_request.id,
                        type=ViolationType.OUT_OF_PATH,
                        location=wkb_point,
                        description="Drone has deviated from approved flight path",
                    )
                    db.add(violation)
                    violations.append(mapping(violation))
            
            
            db.commit()
            
            
            telemetry_data = {
                "type": "telemetry",
                "data": telemetry,
            }
            await broadcast_telemetry(telemetry_data)
            
            if violations:
                violation_data = {
                    "type": "violation",
                    "data": violations,
                }
                await broadcast_telemetry(violation_data)
            
        except Exception as e:
            logger.error(f"Error processing telemetry: {e}")
            db.rollback()
        finally:
            db.close()
    
    def start(self):
        """Start the MQTT client."""
        self.client.loop_start()
    
    def stop(self):
        """Stop the MQTT client."""
        self.client.loop_stop()
        self.client.disconnect()



mqtt_client = MQTTClient() 