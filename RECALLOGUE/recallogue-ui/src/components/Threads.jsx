import React from 'react';

const Threads = ({ currentThread, setCurrentThread, currentThreadDetails, threadsVersion }) => {
  // Mock threads data
  const threads = [
    { id: 1, name: 'Project Discussion', createdAt: '2025-01-15', docCount: 3 },
    { id: 2, name: 'Research Findings', createdAt: '2025-01-14', docCount: 5 },
    { id: 3, name: 'Meeting Notes', createdAt: '2025-01-13', docCount: 2 },
  ];

  return (
    <div className="threads-panel">
      <div className="panel-header">
        <h2>Threads</h2>
        <button className="new-thread-btn" title="New Thread">+</button>
      </div>
      <ul>
        {threads.map((thread) => (
          <li 
            key={thread.id} 
            className={currentThread && currentThread.id === thread.id ? 'active' : ''}
            onClick={() => setCurrentThread(thread)}
          >
            <div className="thread-name">
              <span className="thread-icon">💬</span>
              {thread.name}
            </div>
            <div className="thread-meta">
              <span className="doc-count-badge">{thread.docCount} docs</span>
              <div className="thread-actions">
                <button className="icon-button" title="Rename">✏️</button>
                <button className="icon-button" title="Delete">🗑️</button>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Threads;