import React from 'react';
import { useAuth } from './contexts/AuthContext';
import Login from './components/auth/Login';
import MainApp from './MainApp';

const AppWrapper = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="app-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return <MainApp />;
};

export default AppWrapper;