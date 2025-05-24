import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import Map from '../components/Map';
import { useAuth } from '../hooks/useAuth';


const API_URL = 'http://localhost:8000';


const WS_URL = 'ws://localhost:8000/ws/telemetry';

const MapPage: React.FC = () => {
  const { user } = useAuth();
  const [drones, setDrones] = useState<any[]>([]);
  const [violations, setViolations] = useState<any[]>([]);
  const [socket, setSocket] = useState<WebSocket | null>(null);

  
  const { data: noFlyZones, isLoading: zonesLoading } = useQuery(
    'noFlyZones',
    async () => {
      const response = await axios.get(`${API_URL}/zones`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      return response.data;
    }
  );

  
  const { data: flightPaths, isLoading: pathsLoading } = useQuery(
    'flightPaths',
    async () => {
      const response = await axios.get(`${API_URL}/flights/active`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      return response.data;
    }
  );

  // Connect to WebSocket
  useEffect(() => {
    const newSocket = new WebSocket(WS_URL);
    
    newSocket.onopen = () => {
      console.log('WebSocket connected');
      // You can send initial messages if needed
      newSocket.send(JSON.stringify({ action: 'subscribe' }));
    };
    
    newSocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'telemetry') {
        // Update drone position
        setDrones((prevDrones) => {
          const droneIndex = prevDrones.findIndex(d => d.id === data.data.drone_id);
          if (droneIndex >= 0) {
            // Update existing drone
            const updatedDrones = [...prevDrones];
            updatedDrones[droneIndex] = {
              ...updatedDrones[droneIndex],
              ...data.data,
              hasViolation: violations.some(v => v.drone_id === data.data.drone_id),
            };
            return updatedDrones;
          } else {
            // Add new drone
            return [...prevDrones, data.data];
          }
        });
      } else if (data.type === 'violation') {
        // Handle violation
        setViolations((prev) => [...prev, data.data]);
        
        // Update drone with violation flag
        setDrones((prevDrones) => {
          const droneIndex = prevDrones.findIndex(d => d.id === data.data.drone_id);
          if (droneIndex >= 0) {
            const updatedDrones = [...prevDrones];
            updatedDrones[droneIndex] = {
              ...updatedDrones[droneIndex],
              hasViolation: true,
            };
            return updatedDrones;
          }
          return prevDrones;
        });
        
        // Show notification
        if ('Notification' in window) {
          Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
              new Notification('Drone Violation!', {
                body: `Drone ${data.data.drone_id} has a ${data.data.type} violation`,
                icon: '/logo192.png',
              });
            }
          });
        }
      }
    };
    
    newSocket.onclose = () => {
      console.log('WebSocket disconnected');
      // Attempt to reconnect
      setTimeout(() => {
        setSocket(null);
      }, 5000);
    };
    
    setSocket(newSocket);
    
    return () => {
      newSocket.close();
    };
  }, []);

  const isLoading = zonesLoading || pathsLoading;

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="bg-primary text-white p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Sergex Air UTM</h1>
          <div className="flex items-center space-x-4">
            <span>{user?.full_name}</span>
            <button className="btn bg-white text-primary hover:bg-white/90">
              Dashboard
            </button>
          </div>
        </div>
      </header>
      
      {/* Main content */}
      <main className="flex-1 flex p-4">
        {/* Map container */}
        <div className="flex-1 relative">
          {isLoading ? (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-900 bg-opacity-75 dark:bg-opacity-75 z-10">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
            </div>
          ) : null}
          
          <div className="h-full">
            <Map
              drones={drones}
              noFlyZones={noFlyZones}
              flightPaths={flightPaths}
            />
          </div>
        </div>
        
        {/* Sidebar */}
        <div className="w-80 ml-4 flex flex-col">
          {/* Active drones */}
          <div className="card mb-4 overflow-auto max-h-[50vh]">
            <h2 className="text-lg font-semibold mb-4">Active Drones</h2>
            {drones.length > 0 ? (
              <ul className="space-y-2">
                {drones.map((drone) => (
                  <li key={drone.id} className="p-2 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className="flex items-center">
                      <div className={`w-3 h-3 rounded-full mr-2 ${drone.hasViolation ? 'bg-danger animate-pulse' : 'bg-success'}`}></div>
                      <span className="font-medium">{drone.id}</span>
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      <p>Altitude: {drone.altitude}m</p>
                      <p>Speed: {drone.speed}m/s</p>
                      <p>Status: {drone.status}</p>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 dark:text-gray-400">No active drones</p>
            )}
          </div>
          
          {/* Recent violations */}
          <div className="card flex-1 overflow-auto">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <span>Recent Violations</span>
              {violations.length > 0 && (
                <span className="ml-2 px-2 py-1 text-xs bg-danger text-white rounded-full">
                  {violations.length}
                </span>
              )}
            </h2>
            {violations.length > 0 ? (
              <ul className="space-y-2">
                {violations.map((violation, index) => (
                  <li key={index} className="p-2 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-900/30">
                    <div className="flex justify-between">
                      <span className="font-medium">{violation.drone_id}</span>
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {new Date(violation.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                      {violation.type}: {violation.description}
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 dark:text-gray-400">No violations</p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default MapPage; 