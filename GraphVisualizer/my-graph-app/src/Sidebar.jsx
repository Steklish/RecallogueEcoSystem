import React, { useState, useRef, useEffect } from 'react';

const Sidebar = ({ selectedItem }) => {
  const [sidebarWidth, setSidebarWidth] = useState(300); // Default width
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef(null);
  const resizeRef = useRef(null);

  const startResizing = (e) => {
    setIsResizing(true);
    e.preventDefault();
  };

  const handleMouseMove = (e) => {
    if (!isResizing) return;
    const newWidth = window.innerWidth - e.clientX;
    if (newWidth > 200 && newWidth < 800) { // Min 200px, Max 800px
      setSidebarWidth(newWidth);
    }
  };

  const handleMouseUp = () => {
    setIsResizing(false);
  };

  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  const renderProperties = (properties) => {
    if (!properties || typeof properties !== 'object') return null;

    // Exclude the properties that are already shown separately (name, label)
    const excludeKeys = ['name', 'label'];
    const filteredEntries = Object.entries(properties).filter(([key]) => !excludeKeys.includes(key));

    if (filteredEntries.length === 0) return null;

    return filteredEntries.map(([key, value]) => (
      <div key={key} className="property-item">
        <span className="property-key">{key}:</span>
        <span className="property-value">{typeof value === 'object' && value !== null ? JSON.stringify(value) : value}</span>
      </div>
    ));
  };

  if (!selectedItem) {
    return (
      <div className="sidebar" ref={sidebarRef} style={{ width: `${sidebarWidth}px` }}>
        <div className="resize-handle" ref={resizeRef} onMouseDown={startResizing}></div>
        <h3>Details Panel</h3>
        <p>Select a node or edge to view details</p>
      </div>
    );
  }

  const { type, data } = selectedItem;

  return (
    <div className="sidebar" ref={sidebarRef} style={{ width: `${sidebarWidth}px` }}>
      <div className="resize-handle" ref={resizeRef} onMouseDown={startResizing}></div>
      <h3>{type === 'node' ? 'Node Details' : 'Edge Details'}</h3>

      {type === 'node' ? (
        <div className="node-details">
          <div className="detail-row">
            <strong>Name:</strong>
            <span>{data.attributes?.name || data.properties?.name || 'N/A'}</span>
          </div>
          <div className="detail-row">
            <strong>Type:</strong>
            <span>{data.attributes?.label || data.labels?.[0] || 'N/A'}</span>
          </div>
          <div className="detail-row">
            <strong>ID:</strong>
            <span>{data.key || data.id || 'N/A'}</span>
          </div>

          {(data.attributes || data.properties) && renderProperties(data.attributes || data.properties) && (
            <div className="properties-section">
              <h4>Properties:</h4>
              {renderProperties(data.attributes || data.properties)}
            </div>
          )}
        </div>
      ) : (
        <div className="edge-details">
          <div className="detail-row">
            <strong>Type:</strong>
            <span>{data.attributes?.label || data.type || 'N/A'}</span>
          </div>
          <div className="detail-row">
            <strong>Source:</strong>
            <span>{data.source || 'N/A'}</span>
          </div>
          <div className="detail-row">
            <strong>Target:</strong>
            <span>{data.target || 'N/A'}</span>
          </div>

          {(data.attributes?.reasoning || data.properties?.reasoning) && (
            <div className="detail-row">
              <strong>Reasoning:</strong>
              <span>{data.attributes?.reasoning || data.properties?.reasoning}</span>
            </div>
          )}
          {(data.attributes?.context || data.properties?.context) && (
            <div className="detail-row">
              <strong>Context:</strong>
              <span>{data.attributes?.context || data.properties?.context}</span>
            </div>
          )}
          {(data.attributes?.date || data.properties?.date) && (
            <div className="detail-row">
              <strong>Date:</strong>
              <span>{data.attributes?.date || data.properties?.date}</span>
            </div>
          )}

          {(data.attributes || data.properties) && renderProperties(data.attributes || data.properties) && (
            <div className="properties-section">
              <h4>Properties:</h4>
              {renderProperties(data.attributes || data.properties)}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Sidebar;