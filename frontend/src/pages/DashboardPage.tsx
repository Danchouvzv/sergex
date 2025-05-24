import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <header className="bg-primary text-white p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Sergex Air UTM</h1>
          <div className="flex items-center space-x-4">
            <span>{user?.full_name}</span>
          </div>
        </div>
      </header>
      
      <main className="container mx-auto p-6">
        <h2 className="text-2xl font-bold mb-6">Dashboard</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="card">
            <h3 className="text-xl font-semibold mb-2">Map</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              View and track drones in real-time on the map.
            </p>
            <Link to="/map" className="btn btn-primary">
              View Map
            </Link>
          </div>
          
          <div className="card">
            <h3 className="text-xl font-semibold mb-2">Flight Requests</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Submit and manage flight requests.
            </p>
            <Link to="/flight-request" className="btn btn-primary">
              Flight Requests
            </Link>
          </div>
          
          <div className="card">
            <h3 className="text-xl font-semibold mb-2">Violations</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              View and manage drone violations.
            </p>
            <Link to="/violations" className="btn btn-primary">
              View Violations
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
};

export default DashboardPage; 