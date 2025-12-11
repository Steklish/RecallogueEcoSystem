import React from 'react';

const Sidebar = ({ selectedItem }) => {
  if (!selectedItem) {
    return (
      <div className="sidebar">
        <h3>Details Panel</h3>
        <p>Select a node or edge to view details</p>
      </div>
    );
  }

  const { type, data } = selectedItem;

  return (
    <div className="sidebar">
      <h3>{type === 'node' ? 'Node Details' : 'Edge Details'}</h3>
      
      {type === 'node' ? (
        <div className="node-details">
          <p><strong>Name:</strong> {data.attributes.name || 'N/A'}</p>
          <p><strong>Type:</strong> {data.attributes.label || 'N/A'}</p>
          <p><strong>ID:</strong> {data.key}</p>
        </div>
      ) : (
        <div className="edge-details">
          <p><strong>Type:</strong> {data.attributes.label || 'N/A'}</p>
          <p><strong>Source:</strong> {data.source}</p>
          <p><strong>Target:</strong> {data.target}</p>
          {data.attributes.reasoning && (
            <p><strong>Reasoning:</strong> {data.attributes.reasoning}</p>
          )}
          {data.attributes.context && (
            <p><strong>Context:</strong> {data.attributes.context}</p>
          )}
          {data.attributes.date && (
            <p><strong>Date:</strong> {data.attributes.date}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default Sidebar;