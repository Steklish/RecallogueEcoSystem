import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { LogOut } from 'lucide-react';

const Header = () => {
  const { user, logout } = useAuth();

  if (!user) {
    return null; // Don't show header when not logged in
  }

  const handleLogout = () => {
    logout();
  };

  return (
    <header className="app-header">
      <div className="user-info">
        <span>Welcome, {user.username}</span>
      </div>
      <button className="logout-button" onClick={handleLogout} title="Logout">
        <LogOut size={18} />
        <span>Logout</span>
      </button>
    </header>
  );
};

export default Header;