import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const Settings = ({ disabled }) => {
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="settings-panel">
      <h2>Settings</h2>
      <div className="settings-content">
        <div className="setting-item">
          <h3>General Settings</h3>
          <p>Configure your application settings here.</p>
          <select disabled={disabled}>
            <option>Option 1</option>
            <option>Option 2</option>
            <option>Option 3</option>
          </select>
        </div>

        <div className="setting-item">
          <h3>Model Configuration</h3>
          <p>Manage your AI models and their settings.</p>
          <div className="model-list-container">
            <ul className="model-list">
              <li className="model-item">
                <span className="model-name">GPT-4</span>
                <span className="model-type">Chat Model</span>
                <span className="status-indicator status-running">Running</span>
              </li>
              <li className="model-item">
                <span className="model-name">Ada Embedding</span>
                <span className="model-type">Embedding Model</span>
                <span className="status-indicator status-stopped">Stopped</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="setting-item">
          <h3>Account</h3>
          <div className="button-group">
            <button onClick={handleLogout} disabled={disabled}>
              Logout
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;