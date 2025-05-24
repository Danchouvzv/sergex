import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const ViolationsPage: React.FC = () => {
  const { user } = useAuth();
  
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <header className="bg-primary text-white p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Sergex Air UTM</h1>
          <div className="flex items-center space-x-4">
            <span>{user?.full_name}</span>
            <Link to="/" className="btn bg-white text-primary hover:bg-white/90">
              Dashboard
            </Link>
          </div>
        </div>
      </header>
      
      <main className="container mx-auto p-6">
        <h2 className="text-2xl font-bold mb-6">Violations</h2>
        
        <div className="card">
          <p className="text-center text-gray-600 dark:text-gray-400 py-8">
            Violations page is under development.
          </p>
        </div>
      </main>
    </div>
  );
};

export default ViolationsPage; 