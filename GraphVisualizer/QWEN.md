# Graph Visualizer Application

## Project Overview

The Graph Visualizer is a full-stack web application that provides an interactive graph visualization tool for exploring relationships between entities stored in a Neo4j graph database. The application consists of a Python/FastAPI backend that connects to Neo4j and serves data to a React frontend with interactive network graph visualization capabilities.

The application features dual visualization modes (graph and table), AI-powered query generation from natural language, and detailed entity information display. It was originally named "BeltaScrapper" but serves as a general-purpose graph visualization tool.

## Architecture

### Backend Components
- **Framework**: Python with FastAPI
- **Database**: Neo4j Graph Database (connected via neo4j driver)
- **AI Integration**: Uses Google's Generative AI (Gemini) for natural language to Cypher query conversion
- **Environment**: Uses .env file for configuration

### Frontend Components
- **Framework**: React.js with Vite build tool
- **Visualization**: vis-network for interactive graph rendering
- **UI Components**: 
  - SearchSection with code-editor-like interface
  - NetworkGraph for interactive visualization
  - Sidebar for detailed node/edge information
  - Tabbed interface for graph/table views

## Key Features

### Graph Visualization
- Interactive network graph with color-coded node types
- Automatic color assignment based on entity types
- Curved edges to avoid overlapping
- Clickable nodes and edges for detailed information

### Search & Query Interface
- Code-editor-like search bar with line numbers
- Dual mode: Manual Cypher queries and AI-powered natural language queries
- Tabbed interface switching between Graph and Table views
- Auto-switching to table view when no graph data is returned

### AI Query Generation
- Natural language to Cypher query conversion
- Uses Google's Generative AI with custom prompting
- Predefined schema knowledge for accurate query generation
- Fallback logic for query generation when AI endpoint is unavailable

### Data Handling
- Dual response format: both graph (nodes/edges) and tabular data
- Automatic deduplication of nodes and edges
- Support for Neo4j-specific data types (Node, Relationship, Path)
- Proper handling of different data formats from backend

## API Endpoints

- `POST /api/query` - Execute custom Cypher queries, returns both graph and table data
- `GET /api/graph` - Return predefined graph data (initial dataset)
- `POST /api/reques_query` - Convert natural language to Cypher query using AI

## File Structure

```
D:\Duty\GraphVisualizer\
├── web.py (Main FastAPI backend application)
├── generate_cypher.py (AI query generation models and requester)
├── generator.py (Generator interface for AI models)
├── google_gen.py (Google Generative AI implementation)
├── logger_config.py (Logging configuration)
├── generate_cypher.py (Query models)
├── __pycache__/ (Python cache)
├── log/ (Log files directory)
├── .gitignore (Git ignore rules)
├── README.md (Project documentation)
├── QWEN.md (Current file)
└── my-graph-app/ (React frontend)
    ├── package.json (Dependencies and scripts)
    ├── vite.config.js (Vite build configuration)
    ├── index.html (HTML entry point)
    ├── node_modules/ (NPM packages)
    └── src/ (Source code)
        ├── App.jsx (Main application component)
        ├── NetworkGraph.jsx (Graph visualization component)
        ├── SearchSection.jsx (Search interface component)
        ├── Sidebar.jsx (Information sidebar component)
        └── index.css (CSS styles and theming)
```

## Setup and Running Instructions

### Backend Setup
1. Install Python dependencies:
   ```bash
   pip install fastapi neo4j python-dotenv uvicorn
   ```

2. Create a `.env` file with:
   ```
   URI=bolt://localhost:7687
   USER=neo4j
   PASSWORD=11111111
   GEMINI_API_KEY=your_api_key_here
   ```

3. Start the backend server:
   ```bash
   python -m uvicorn web:app --host 127.0.0.1 --port 8000 --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd my-graph-app
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

### System Requirements
- Neo4j database running at bolt://localhost:7687 with credentials
- Python 3.8+ for backend
- Node.js 16+ for frontend
- Google Generative AI API key for AI features

## Development Conventions

### Frontend Styling
- Dark theme interface with specific color palette (defined in README)
- Responsive design using flexbox layout
- Consistent styling for all interactive elements
- Custom scrollbar styling for better UI consistency

### Code Structure
- React components with clear separation of concerns
- Proper cleanup of resources (especially vis-network instances)
- Error handling for both frontend and backend operations
- State management using React hooks
- Asynchronous operations with proper error handling

### Data Flow
- Backend processes Neo4j Result objects into standardized format
- Frontend handles multiple data formats (with attributes vs with properties)
- Proper deduplication of graph elements
- Tab switching based on available data types

## Color Schema
- Background: `#1c1c1e`
- Text: `#e1e1e0`
- Primary: `#a9967f`
- Panel backgrounds: `#2a2a2c`, `#252526`
- Input areas: `#3a3a3c`

## Entity Type Colors
The application uses a predefined color palette for different entity types:
- Intense Cherry: `#c33149ff`
- Smoky Rose: `#7b5c60ff` 
- Jungle Teal: `#338776ff`
- And more for consistent visualization