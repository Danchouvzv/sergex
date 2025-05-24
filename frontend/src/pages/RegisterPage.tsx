import React from 'react';
import { Link } from 'react-router-dom';

const RegisterPage: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900 p-4">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary">Sergex Air UTM</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Drone Traffic Management System
          </p>
        </div>

        <h2 className="text-2xl font-semibold mb-6">Register</h2>
        
        <p className="text-center text-gray-600 dark:text-gray-400">
          Registration page is under development.
        </p>
        
        <div className="mt-6 text-center">
          <p className="text-gray-600 dark:text-gray-400">
            Already have an account?{' '}
            <Link to="/login" className="text-primary hover:underline">
              Log In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage; 