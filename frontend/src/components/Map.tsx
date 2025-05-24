import React, { useRef, useEffect, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Feature, FeatureCollection, Point } from 'geojson';


mapboxgl.accessToken = 'YOUR_MAPBOX_ACCESS_TOKEN';

interface DroneData {
  id: string;
  location: {
    type: string;
    coordinates: [number, number]; 
  };
  altitude: number;
  speed: number;
  heading?: number;
  status: string;
  hasViolation?: boolean;
}

interface MapProps {
  center?: [number, number];
  zoom?: number;
  drones?: DroneData[];
  noFlyZones?: GeoJSON.FeatureCollection;
  flightPaths?: GeoJSON.FeatureCollection;
  onMapClick?: (e: mapboxgl.MapMouseEvent) => void;
}

const Map: React.FC<MapProps> = ({
  center = [71.4491, 51.1694], // Астана 
  zoom = 12,
  drones = [],
  noFlyZones,
  flightPaths,
  onMapClick,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  
  
  useEffect(() => {
    if (!mapContainer.current) return;
    
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v11',
      center,
      zoom,
    });

    map.current.on('load', () => {
      setMapLoaded(true);
      
      
      map.current?.addControl(new mapboxgl.NavigationControl(), 'top-right');
      
      
      map.current?.addControl(new mapboxgl.ScaleControl(), 'bottom-left');
    });

    if (onMapClick) {
      map.current.on('click', onMapClick);
    }

    return () => {
      map.current?.remove();
    };
  }, []);

  
  useEffect(() => {
    if (!mapLoaded || !map.current || !noFlyZones) return;

    
    if (!map.current.getSource('no-fly-zones')) {
      map.current.addSource('no-fly-zones', {
        type: 'geojson',
        data: noFlyZones,
      });

      
      map.current.addLayer({
        id: 'no-fly-zones-fill',
        type: 'fill',
        source: 'no-fly-zones',
        paint: {
          'fill-color': '#FF5F57',
          'fill-opacity': 0.3,
        },
      });

      
      map.current.addLayer({
        id: 'no-fly-zones-outline',
        type: 'line',
        source: 'no-fly-zones',
        paint: {
          'line-color': '#FF5F57',
          'line-width': 2,
        },
      });
    } else {
      
      (map.current.getSource('no-fly-zones') as mapboxgl.GeoJSONSource).setData(
        noFlyZones
      );
    }
  }, [mapLoaded, noFlyZones]);

  
  useEffect(() => {
    if (!mapLoaded || !map.current || !flightPaths) return;

    
    if (!map.current.getSource('flight-paths')) {
      map.current.addSource('flight-paths', {
        type: 'geojson',
        data: flightPaths,
      });

      // Add line layer
      map.current.addLayer({
        id: 'flight-paths-line',
        type: 'line',
        source: 'flight-paths',
        paint: {
          'line-color': [
            'match',
            ['get', 'status'],
            'approved', '#28A745',
            'pending', '#FFC107',
            'rejected', '#FF5F57',
            '#0056C7' // Default
          ],
          'line-width': 3,
          'line-dasharray': [
            'match',
            ['get', 'status'],
            'approved', [1, 0],
            'pending', [2, 1],
            [1, 0] // Default
          ],
        },
      });
    } else {
      // Update source data
      (map.current.getSource('flight-paths') as mapboxgl.GeoJSONSource).setData(
        flightPaths
      );
    }
  }, [mapLoaded, flightPaths]);

  // Update drone markers
  useEffect(() => {
    if (!mapLoaded || !map.current) return;

    // Convert drones to GeoJSON
    const droneFeatures: Feature<Point>[] = drones.map((drone) => ({
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: drone.location.coordinates,
      },
      properties: {
        id: drone.id,
        altitude: drone.altitude,
        speed: drone.speed,
        heading: drone.heading || 0,
        status: drone.status,
        hasViolation: drone.hasViolation || false,
      },
    }));

    const droneCollection: FeatureCollection<Point> = {
      type: 'FeatureCollection',
      features: droneFeatures,
    };

    // Add drones source if it doesn't exist
    if (!map.current.getSource('drones')) {
      map.current.addSource('drones', {
        type: 'geojson',
        data: droneCollection,
      });

      // Add drone symbol layer
      map.current.addLayer({
        id: 'drones-symbol',
        type: 'symbol',
        source: 'drones',
        layout: {
          'icon-image': 'airport-15',
          'icon-size': 1.5,
          'icon-allow-overlap': true,
          'icon-rotate': ['get', 'heading'],
          'text-field': ['get', 'id'],
          'text-offset': [0, 1.5],
          'text-size': 12,
        },
        paint: {
          'icon-color': [
            'case',
            ['get', 'hasViolation'], '#FF5F57',
            '#0056C7'
          ],
          'text-color': '#000000',
          'text-halo-color': '#FFFFFF',
          'text-halo-width': 1,
        },
      });

      
      map.current.on('mouseenter', 'drones-symbol', (e) => {
        if (!e.features || !e.features[0]) return;
        
        const coordinates = (e.features[0].geometry as Point).coordinates.slice() as [number, number];
        const { id, altitude, speed, status } = e.features[0].properties || {};
        
        const html = `
          <div>
            <h3 class="font-bold">${id}</h3>
            <p>Altitude: ${altitude}m</p>
            <p>Speed: ${speed}m/s</p>
            <p>Status: ${status}</p>
          </div>
        `;
        
        new mapboxgl.Popup()
          .setLngLat(coordinates)
          .setHTML(html)
          .addTo(map.current as mapboxgl.Map);
      });
      
      
      map.current.on('mouseleave', 'drones-symbol', () => {
        (map.current as mapboxgl.Map).getCanvas().style.cursor = '';
        
        const popups = document.getElementsByClassName('mapboxgl-popup');
        if (popups.length) {
          (popups[0] as HTMLElement).remove();
        }
      });
    } else {
      
      (map.current.getSource('drones') as mapboxgl.GeoJSONSource).setData(
        droneCollection
      );
    }
  }, [mapLoaded, drones]);

  return (
    <div ref={mapContainer} className="h-full w-full rounded-xl overflow-hidden" />
  );
};

export default Map; 