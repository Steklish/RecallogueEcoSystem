import React, { useState, useEffect, useCallback } from 'react';
import NetworkGraph from './NetworkGraph.jsx';
import SearchSection from './SearchSection.jsx';
import Sidebar from './Sidebar.jsx';
import './index.css';

function App() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [selectedItem, setSelectedItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [activeTab, setActiveTab] = useState('graph'); // 'graph' or 'table'
  const [searchLoading, setSearchLoading] = useState(false);

  useEffect(() => {
    // Fetch graph data from the backend API
    const fetchGraphData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/graph');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setGraphData(data);

        // Log nodes and edges count after loading
        console.log(`Loaded graph data: ${data.nodes.length} nodes, ${data.edges.length} edges`);

        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
        console.error('Error fetching graph data:', err);
      }
    };

    fetchGraphData();
  }, []);

  const handleSearch = async (query) => {
    if (!query.trim()) return;

    setSearchLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSearchResults(data);
      setActiveTab('table'); // Switch to table view when search results are available
    } catch (err) {
      setError(err.message);
      console.error('Error searching:', err);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleNodeSelect = useCallback((nodeData) => {
    if (nodeData === null) {
      setSelectedItem(null);
    } else {
      setSelectedItem({ type: 'node', data: nodeData });
    }
  }, []);

  const handleEdgeSelect = useCallback((edgeData) => {
    if (edgeData) {
      setSelectedItem({ type: 'edge', data: edgeData });
    } else {
      setSelectedItem(null);
    }
  }, []);

  if (loading) {
    return <div className="app-loading">Loading graph data...</div>;
  }

  if (error && !searchLoading) {
    return (
      <div className="app-error">
        <h2>Error loading graph data</h2>
        <p>{error}</p>
        <p>Make sure the backend server is running on http://localhost:8000</p>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="app-container">
        <SearchSection
          onSearch={handleSearch}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />

        <div className="main-content">
          <div className="visualization-container">
            {searchLoading ? (
              <div className="search-loading">Searching...</div>
            ) : (
              <>
                {activeTab === 'graph' ? (
                  <NetworkGraph
                    data={graphData}
                    onNodeSelect={handleNodeSelect}
                    onEdgeSelect={handleEdgeSelect}
                  />
                ) : (
                  <div className="table-visualization">
                    <h3>Search Results</h3>
                    {searchResults ? (
                      <div className="results-container">
                        {searchResults.nodes && searchResults.nodes.length > 0 && (
                          <div className="results-section">
                            <h4>Nodes</h4>
                            <table className="results-table">
                              <thead>
                                <tr>
                                  <th>ID</th>
                                  <th>Name</th>
                                  <th>Label</th>
                                </tr>
                              </thead>
                              <tbody>
                                {searchResults.nodes.map((node) => (
                                  <tr
                                    key={node.key}
                                    onClick={() => setSelectedItem({ type: 'node', data: node })}
                                    className="table-row-clickable"
                                  >
                                    <td>{node.key}</td>
                                    <td>{node.attributes.name}</td>
                                    <td>{node.attributes.label}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                        {searchResults.edges && searchResults.edges.length > 0 && (
                          <div className="results-section">
                            <h4>Edges</h4>
                            <table className="results-table">
                              <thead>
                                <tr>
                                  <th>ID</th>
                                  <th>Source</th>
                                  <th>Target</th>
                                  <th>Label</th>
                                </tr>
                              </thead>
                              <tbody>
                                {searchResults.edges.map((edge) => (
                                  <tr
                                    key={edge.key}
                                    onClick={() => setSelectedItem({ type: 'edge', data: edge })}
                                    className="table-row-clickable"
                                  >
                                    <td>{edge.key}</td>
                                    <td>{edge.source}</td>
                                    <td>{edge.target}</td>
                                    <td>{edge.attributes.label}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                        {!searchResults.nodes && !searchResults.edges && (
                          <p>No results found</p>
                        )}
                      </div>
                    ) : (
                      <p>Run a search to see results</p>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
          <Sidebar selectedItem={selectedItem} />
        </div>
      </div>
    </div>
  );
}

export default App;