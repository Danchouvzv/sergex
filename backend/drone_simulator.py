#!/usr/bin/env python3
"""
Drone Simulator - Emulates drone movement and sends telemetry via MQTT
"""

import json
import time
import uuid
import random
import argparse
from datetime import datetime
from typing import Dict, List, Tuple

import paho.mqtt.client as mqtt
from shapely.geometry import LineString, Point
import numpy as np


class DroneSimulator:
    """Simulates drone movement along a path and sends telemetry via MQTT."""
    
    def __init__(
        self,
        drone_id: str,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        topic_prefix: str = "drones",
    ):
        """Initialize the drone simulator."""
        self.drone_id = drone_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = f"{topic_prefix}/{drone_id}/telemetry"
        
        # Connect to MQTT broker
        self.client = mqtt.Client(f"drone-sim-{drone_id}")
        self.client.connect(broker_host, broker_port)
        
        # Default values
        self.altitude = 100.0  # meters
        self.speed = 10.0  # m/s
        self.battery_level = 100.0  # percentage
        self.status = "flying"
    
    def generate_random_path(
        self, 
        center_lat: float = 51.1694, 
        center_lon: float = 71.4491,  # Astana coordinates
        radius: float = 0.05,
        num_points: int = 10
    ) -> LineString:
        """Generate a random path around a center point."""
        points = []
        for _ in range(num_points):
            # Random point within radius
            angle = random.uniform(0, 2 * np.pi)
            r = random.uniform(0, radius)
            lat = center_lat + r * np.cos(angle)
            lon = center_lon + r * np.sin(angle)
            points.append((lon, lat))  # GeoJSON is (lon, lat)
        
        return LineString(points)
    
    def simulate_flight(self, path: LineString, duration: int = 60, interval: float = 1.0):
        """Simulate flight along a path for a specified duration."""
        print(f"Simulating flight for drone {self.drone_id}")
        print(f"Path: {path}")
        
        # Extract coordinates from path
        coords = list(path.coords)
        num_segments = len(coords) - 1
        
        # Calculate time per segment
        time_per_segment = duration / num_segments
        
        # Simulate movement along each segment
        for i in range(num_segments):
            start_point = Point(coords[i])
            end_point = Point(coords[i+1])
            
            # Calculate number of steps for this segment
            distance = start_point.distance(end_point) * 111000  # approx meters
            steps = max(1, int(time_per_segment / interval))
            
            # Simulate steps along the segment
            for step in range(steps):
                # Interpolate position
                fraction = step / steps
                current_lon = coords[i][0] + fraction * (coords[i+1][0] - coords[i][0])
                current_lat = coords[i][1] + fraction * (coords[i+1][1] - coords[i][1])
                
                # Simulate some altitude variation
                self.altitude += random.uniform(-1, 1)
                
                # Simulate battery drain
                self.battery_level -= 0.01
                
                # Create telemetry data
                telemetry = {
                    "drone_id": self.drone_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "location": {
                        "type": "Point",
                        "coordinates": [current_lon, current_lat]
                    },
                    "altitude": self.altitude,
                    "speed": self.speed,
                    "heading": random.uniform(0, 360),
                    "battery_level": self.battery_level,
                    "status": self.status
                }
                
                # Send telemetry via MQTT
                self.client.publish(self.topic, json.dumps(telemetry))
                print(f"Published: {json.dumps(telemetry)}")
                
                # Wait for the next interval
                time.sleep(interval)
    
    def close(self):
        """Disconnect from MQTT broker."""
        self.client.disconnect()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Drone Telemetry Simulator")
    parser.add_argument("--drone-id", type=str, default=str(uuid.uuid4()), help="Drone ID")
    parser.add_argument("--broker-host", type=str, default="localhost", help="MQTT broker host")
    parser.add_argument("--broker-port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--duration", type=int, default=60, help="Simulation duration in seconds")
    parser.add_argument("--interval", type=float, default=1.0, help="Telemetry interval in seconds")
    args = parser.parse_args()
    
    # Create drone simulator
    simulator = DroneSimulator(
        drone_id=args.drone_id,
        broker_host=args.broker_host,
        broker_port=args.broker_port,
    )
    
    try:
        # Generate random path and simulate flight
        path = simulator.generate_random_path()
        simulator.simulate_flight(path, args.duration, args.interval)
    except KeyboardInterrupt:
        print("Simulation interrupted")
    finally:
        simulator.close()


if __name__ == "__main__":
    main() 