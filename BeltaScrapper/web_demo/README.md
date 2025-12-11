# BeltaScrapper Web Application

## Overview
The BeltaScrapper web application is a graph visualization tool that displays relationships between entities (People and Organizations) fetched from a backend API. The application consists of a React frontend with a network graph visualization and backend API server.

## Architecture

### Frontend
- **Framework**: React.js with Vite as the build tool
- **Visualization**: vis-network for graph rendering
- **Components**:
  - `App`: Main application component
  - `NetworkGraph`: Interactive network visualization
  - `SearchSection`: Search functionality (assumed from imports)
  - `Sidebar`: Information panel (assumed from imports)

### Backend
- **Framework**: Python with Flask/FastAPI (based on web.py)
- **API Endpoint**: `/api/graph` - serves graph data to the frontend

## Current Functionality

### Data Flow
1. On application load, the frontend fetches graph data from `http://localhost:8000/api/graph`
2. The data contains nodes (People and Organizations) and edges (relationships)
3. The NetworkGraph component processes and visualizes this data as an interactive network
4. Users can click on nodes and edges to view details in the sidebar

### Graph Visualization
- **Nodes**:
  - People: Represented as dots with beige/golden border
  - Organizations: Represented as boxes with gray border
- **Edges**:
  - Lines connecting related nodes
  - Curved to avoid overlapping
  - Optionally labeled with relationship types
- **Interactions**:
  - Click on nodes/edges to view details
  - Drag to move nodes
  - Zoom in/out to navigate large graphs

### Styling
- Dark theme interface with gray backgrounds and beige accents
- Consistent arrow styling for all directed relationships
- Responsive design that fills available space

## Key Features

1. **Real-time Graph Visualization**: Instantly displays relationship data from the backend
2. **Interactive Exploration**: Users can click and navigate the graph
3. **Entity Differentiation**: Clear visual distinction between people and organizations
4. **Relationship Mapping**: Shows how entities are connected in the network

## Technical Implementation Notes

### NetworkGraph Component
- Uses `vis-network` (standalone version) for visualization
- Completely recreates the network when data changes to avoid rendering issues
- Processes data to extract node labels, types, and relationship information
- Handles node and edge selection events
- Implements proper cleanup to prevent memory leaks

### Data Structure
- **Nodes**: Have `key`, `attributes.name`, and `attributes.label` properties
- **Edges**: Have `key`, `source`, `target`, and `attributes.label` properties
- The backend provides this structured data via the `/api/graph` endpoint

## File Structure
```
web_demo/
├── web.py (Backend API server)
└── react/
    └── my-graph-app/
        ├── app.jsx (Main React component)
        ├── NetworkGraph.jsx (Visualization component)
        └── (other React app files)
```

## Setup Requirements
- Backend server running on `http://localhost:8000`
- Frontend development server for React application
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