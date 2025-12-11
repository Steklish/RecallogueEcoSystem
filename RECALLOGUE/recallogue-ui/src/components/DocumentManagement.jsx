import React from 'react';

const DocumentManagement = ({ currentThread, onThreadUpdate, onDocumentChange }) => {
  return (
    <div className="document-management-panel">
      <h2>Documents</h2>
      <div className="document-list">
        <div className="empty-state">
          <p>No documents uploaded yet</p>
        </div>
        <div className="dropzone">
          <p>Drag & drop documents here or click to browse</p>
        </div>
      </div>
    </div>
  );
};

export default DocumentManagement;