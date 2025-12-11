import React, { useState, useEffect, useCallback } from 'react';
import NetworkGraph from './NetworkGraph.jsx';
import SearchSection from './SearchSection.jsx';
import Sidebar from './Sidebar.jsx';
import './index.css';

function App() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [selectedItem, setSelectedItem] = useState(null);
  const [loading, setLoading] = useState(false); // No initial loading
  const [error, setError] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [activeTab, setActiveTab] = useState('graph'); // 'graph' or 'table'
  const [searchLoading, setSearchLoading] = useState(false);

  // Removed initial data loading - wait for user search instead

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

      // Update the search results first
      setSearchResults(data);

      // Determine which tab should be active based on the returned data
      let newActiveTab = activeTab; // Default to current tab

      // If there's graph data, check if it contains nodes/edges
      if (data.graph) {
        setGraphData(data.graph);

        const hasNodes = data.graph.nodes && data.graph.nodes.length > 0;
        const hasEdges = data.graph.edges && data.graph.edges.length > 0;

        // If no nodes and no edges but we have table data, switch to table view
        if (!hasNodes && !hasEdges && data.table && data.table.length > 0) {
          newActiveTab = 'table';
        } else if (!hasNodes && !hasEdges && !data.table) {
          // If no nodes, edges, and no table data, still show table view to inform user
          newActiveTab = 'table';
        }
        // If there are nodes/edges, keep the current tab (graph or table)
      } else if (data.table && data.table.length > 0) {
        // If no graph data but table data exists, show table view
        newActiveTab = 'table';
      } else {
        // If no data at all, show table view
        newActiveTab = 'table';
      }

      setActiveTab(newActiveTab);
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

  // No initial loading/error handling since we don't load on startup

  return (
    <div className="app">
      <div className="app-container">
        <div className="search-and-tabs-container">
          <SearchSection
            onSearch={handleSearch}
          />
          {/* Tab switch next to the search bar */}
          <div className="tab-switch-container">
            <div className={`tab-switch ${activeTab === 'graph' ? 'active' : ''}`} onClick={() => setActiveTab('graph')}>
              Graph
            </div>
            <div className={`tab-switch ${activeTab === 'table' ? 'active' : ''}`} onClick={() => setActiveTab('table')}>
              Table
            </div>
          </div>
        </div>

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
                        {searchResults.graph && searchResults.graph.nodes && searchResults.graph.nodes.length > 0 && (
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
                                {searchResults.graph.nodes.map((node) => (
                                  <tr
                                    key={node.id ? node.id : node.key}
                                    onClick={() => setSelectedItem({ type: 'node', data: node })}
                                    className="table-row-clickable"
                                  >
                                    <td>{node.id ? node.id : node.key}</td>
                                    <td>{node.properties ? node.properties.name : (node.attributes ? node.attributes.name : 'N/A')}</td>
                                    <td>{node.labels ? node.labels.join(', ') : (node.attributes ? node.attributes.label : 'N/A')}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                        {searchResults.graph && searchResults.graph.edges && searchResults.graph.edges.length > 0 && (
                          <div className="results-section">
                            <h4>Edges</h4>
                            <table className="results-table">
                              <thead>
                                <tr>
                                  <th>Type</th>
                                  <th>Reasoning</th>
                                </tr>
                              </thead>
                              <tbody>
                                {searchResults.graph.edges.map((edge) => (
                                  <tr
                                    key={edge.id ? edge.id : edge.key}
                                    onClick={() => setSelectedItem({ type: 'edge', data: edge })}
                                    className="table-row-clickable"
                                  >
                                    <td>{edge.type ? edge.type : (edge.attributes ? edge.attributes.label : 'N/A')}</td>
                                    <td>{edge.properties ? edge.properties.reasoning : (edge.attributes ? edge.attributes.reasoning : 'N/A')}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                        {searchResults.table && searchResults.table.length > 0 && (
                          <div className="results-section">
                            <h4>Raw Data</h4>
                            <table className="results-table">
                              <thead>
                                <tr>
                                  {/* Generate headers from the keys in the first row */}
                                  {searchResults.table[0] && Object.keys(searchResults.table[0]).map((key) => (
                                    <th key={key}>{key}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {searchResults.table.map((row, index) => (
                                  <tr
                                    key={index}
                                    className="table-row-clickable"
                                  >
                                    {row && Object.values(row).map((value, idx) => (
                                      <td key={idx}>{typeof value === 'object' ? JSON.stringify(value) : value}</td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                        {!searchResults.graph && !searchResults.table && (
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