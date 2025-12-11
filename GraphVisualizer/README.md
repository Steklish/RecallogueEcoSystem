# BeltaScrapper Web Application

## Overview
The BeltaScrapper web application is a graph visualization tool that displays relationships between entities (People and Organizations) fetched from a backend API. The application consists of a React frontend with a network graph visualization and FastAPI backend server.

## Architecture

### Frontend
- **Framework**: React.js with Vite as the build tool
- **Visualization**: vis-network for graph rendering
- **Components**:
  - `App`: Main application component
  - `NetworkGraph`: Interactive network visualization
  - `SearchSection`: Search functionality with tabbed interface
  - `Sidebar`: Information panel for node/edge details

### Backend
- **Framework**: Python with FastAPI (based on web.py)
- **API Endpoint**: `/api/query` - serves graph and tabular data to the frontend
- **Database**: Neo4j graph database connection

## Current Functionality

### Data Flow
1. On application load, the frontend fetches initial graph data from `http://localhost:8000/api/query` with a default query
2. The data contains nodes (People and Organizations) and edges (relationships)
3. Custom Cypher queries can be executed via the search interface
4. The NetworkGraph component processes and visualizes graph data as an interactive network
5. Users can click on nodes and edges to view details in the sidebar
6. Tabular data from queries is displayed in table view

### Graph Visualization
- **Nodes**:
  - Different entity types (Person, Organization, etc.) represented with different colors
  - Labels displayed inside nodes
  - Clickable for detailed information
- **Edges**:
  - Lines connecting related nodes
  - Curved to avoid overlapping
  - Labeled with relationship types
- **Interactions**:
  - Click on nodes/edges to view details
  - Drag to move nodes
  - Zoom in/out to navigate large graphs

### Search & Query Interface
- Execute custom Cypher queries against the Neo4j database
- Switch between graph and table visualizations
- View both graph data and raw tabular results from queries

### Styling
- Dark theme interface with gray backgrounds and beige accents
- Consistent arrow styling for all directed relationships
- Responsive design that fills available space

## Key Features

1. **Real-time Graph Visualization**: Instantly displays relationship data from the backend
2. **Interactive Exploration**: Users can click and navigate the graph
3. **Entity Differentiation**: Color-coded entities based on type
4. **Relationship Mapping**: Shows how entities are connected in the network
5. **Custom Querying**: Execute custom Cypher queries with live results
6. **Dual Visualizations**: Switch between graph and table views
7. **Detailed Information**: Sidebar shows properties and details for selected elements

## Technical Implementation Notes

### Data Flow
- Backend processes Neo4j Result objects into generic format with deduplication
- Returns both graph data (nodes/edges) and tabular data from queries
- Frontend handles Neo4j-specific data types (Node, Relationship, Path)

### NetworkGraph Component
- Uses `vis-network` (standalone version) for visualization
- Completely recreates the network when data changes to avoid rendering issues
- Processes data to extract node labels, types, and relationship information
- Handles node and edge selection events
- Implements proper cleanup to prevent memory leaks
- Uses predefined color palette for consistent entity type visualization

### Data Structure
- **Nodes**: Have `id`, `labels`, and `properties` properties
- **Edges**: Have `id`, `source`, `target`, and `type` properties
- The backend processes different Neo4j data types (Node, Relationship, Path) into standardized format

## API Endpoints

- `POST /api/query`: Execute custom Cypher queries, returns both graph and table data
  - Request body: `{ "query": "YOUR_CYPHER_QUERY" }`
  - Response: `{ "graph": { "nodes": [...], "edges": [...] }, "table": [...] }`

## File Structure
```
D:\Duty\GraphVisualizer\
├── web.py (FastAPI backend)
└── my-graph-app/ (React frontend)
    ├── src/
    │   ├── App.jsx (Main component)
    │   ├── NetworkGraph.jsx (Visualization)
    │   ├── SearchSection.jsx (Query input)
    │   └── Sidebar.jsx (Detail panel)
    ├── package.json (Dependencies)
    └── index.html (Entry point)
```

## Setup Requirements
- Backend server running on `http://localhost:8000`
- Frontend development server for React application
- Neo4j database running on `bolt://localhost:7687` with credentials
- Network access between frontend and backend


## Color schema

  --background-color: #1c1c1e;
  --text-color: #e1e1e0;
  --primary-color: #a9967f;
  --primary-color-fade: #7b7061;
  --border-color: #3a3a3c;
  --panel-background: #2a2a2c;
  --panel-background-fade: #252526;
  --input-background: #3a3a3c;
  --hover-color: #4a4a4c;
  --message-user-background: #3a3a3c;
  --message-bot-background: #2a2a2c;
  --success-color: #71b34f;
  --error-color: #F44336;
  --accent-color: #3a3a3a;

## Entity colors


  /* CSS HEX */
--intense-cherry: #c33149ff;
--smoky-rose: #7b5c60ff;
--jungle-teal: #338776ff;
--jungle-green: #46ac67ff;
--yellow-green: #a8c256ff;
--golden-sand: #cece84ff;
--wheat: #f3d9b1ff;
--camel: #c29979ff;
--terracotta-clay: #b25f4eff;
--brown-red: #a22522ff;

# Heatmap gradient

/* SCSS HEX */
$shamrock: #3a9e6cff;
$sage-green: #74ae63ff;
$muted-olive: #aebe59ff;
$sunlit-clay: #f5b560ff;
$burnt-peach: #dd784cff;
$fiery-terracotta: #de533cff;
$racing-red: #df2e2bff;