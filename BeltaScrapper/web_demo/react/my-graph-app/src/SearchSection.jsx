import React, { useState } from 'react';

const SearchSection = ({ onSearch, activeTab, onTabChange }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    onSearch(searchTerm);
  };

  return (
    <div className="search-section">
      <form onSubmit={handleSearch} className="search-form">
        <textarea
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Enter your query here..."
          className="search-textarea"
          rows="3"
        />
        <button type="submit" className="search-button">
          Search
        </button>
      </form>

      <div className="tabs">
        <button
          className={`tab-button ${activeTab === 'graph' ? 'active' : ''}`}
          onClick={() => onTabChange('graph')}
        >
          Graph Visualization
        </button>
        <button
          className={`tab-button ${activeTab === 'table' ? 'active' : ''}`}
          onClick={() => onTabChange('table')}
        >
          Table/Raw Visualization
        </button>
      </div>
    </div>
  );
};

export default SearchSection;