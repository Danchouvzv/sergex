import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';


import LoginPage from './pages/LoginPage.tsx';
import RegisterPage from './pages/RegisterPage.tsx';
import DashboardPage from './pages/DashboardPage.tsx';
import MapPage from './pages/MapPage.tsx';
import FlightRequestPage from './pages/FlightRequestPage.tsx';
import ViolationsPage from './pages/ViolationsPage.tsx';
import NotFoundPage from './pages/NotFoundPage.tsx';


import PrivateRoute from './components/PrivateRoute.tsx';


import { AuthProvider } from './hooks/useAuth.tsx';


const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
          <Routes>
            
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            
            
            <Route path="/" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
            <Route path="/map" element={<PrivateRoute><MapPage /></PrivateRoute>} />
            <Route path="/flight-request" element={<PrivateRoute><FlightRequestPage /></PrivateRoute>} />
            <Route path="/violations" element={<PrivateRoute><ViolationsPage /></PrivateRoute>} />
            
            
            <Route path="/404" element={<NotFoundPage />} />
            <Route path="*" element={<Navigate to="/404" replace />} />
          </Routes>
        </div>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App; 