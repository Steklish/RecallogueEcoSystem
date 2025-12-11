import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase, basic_auth
from dotenv import load_dotenv
from neo4j.graph import Node, Relationship, Path
from generate_cypher import Query, Requester, QueryAI
from dotenv import load_dotenv

from generator import Generator
from google_gen import GoogleGenAI
load_dotenv(override=True)
# 1. Load Environment Variables (Create a .env file or set these manually)
# load_dotenv()
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "11111111"

# 2. Database Connection Management
driver = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create driver
    global driver
    driver = GraphDatabase.driver(URI, auth=basic_auth(USER, PASSWORD))
    print(f"Connected to Neo4j at {URI}")
    yield
    # Shutdown: Close driver
    if driver:
        driver.close()

app = FastAPI(lifespan=lifespan, debug=True)

# 3. CORS Setup (Crucial for Sigma.js on localhost:3000 to talk to Python on localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_all_labels():
    # 2. Connect to the database
    with GraphDatabase.driver(URI, auth=basic_auth(USER, PASSWORD)) as driver:
        driver.verify_connectivity()
        
        # 3. Execute the Cypher query
        # "CALL db.labels()" is the most efficient way to get all labels
        records, summary, keys = driver.execute_query(
            "CALL db.labels() YIELD label RETURN label ORDER BY label",
            database_="neo4j",  # Change if using a different database name
        )

        # 4. Extract labels from the result records
        # Each 'record' is like a dictionary where the key is the column name ('label')
        labels = [record["label"] for record in records]
        print(f"Found {len(labels)} labels:")
        print(labels)
        return labels


requester = Requester(
    generator=Generator(client=GoogleGenAI(os.getenv("GEMINI_API_KEY"))), 
    labels=get_all_labels()
)


def process_neo4j_results(result):
    """
    Parses a Neo4j Result object into a generic format for the frontend.
    Deduplicates nodes and edges.
    """
    
    # Use dictionaries for deduplication (Key = Element ID)
    nodes_map = {}
    edges_map = {}
    
    # List to hold non-graph tabular data
    table_data = []

    for record in result:
        row_data = {}
        
        # Iterate over every key-value pair in the row
        for key, value in record.items():
            
            # --- CHECK FOR GRAPH DATA ---
            
            # 1. Is it a Node?
            if isinstance(value, Node):
                nodes_map[value.element_id] = {
                    "id": value.element_id,
                    "labels": list(value.labels), # Convert frozenset to list
                    "properties": dict(value)
                }
                # For the table view, we might just want a string rep
                row_data[key] = f"Node({value.element_id})"

            # 2. Is it a Relationship?
            elif isinstance(value, Relationship):
                edges_map[value.element_id] = {
                    "id": value.element_id,
                    "source": value.start_node.element_id, # type: ignore
                    "target": value.end_node.element_id, # type: ignore
                    "type": value.type,
                    "properties": dict(value)
                }
                row_data[key] = f"Rel({value.type})"

            # 3. Is it a Path? (A container of Nodes and Rels)
            elif isinstance(value, Path):
                for node in value.nodes:
                    nodes_map[node.element_id] = {
                        "id": node.element_id,
                        "labels": list(node.labels),
                        "properties": dict(node)
                    }
                for rel in value.relationships:
                    edges_map[rel.element_id] = {
                        "id": rel.element_id,
                        "source": rel.start_node.element_id, # type: ignore
                        "target": rel.end_node.element_id, # type: ignore
                        "type": rel.type,
                        "properties": dict(rel)
                    }
                row_data[key] = f"Path(len={len(value)})"

            # 4. Is it a List? (Might contain Nodes/Rels)
            elif isinstance(value, list):
                # You might want to recursively check lists here 
                # strictly for visualization extraction
                row_data[key] = value

            # --- OTHERWISE IT IS SCALAR DATA ---
            else:
                # Strings, Ints, Maps, Dates
                row_data[key] = value
        
        table_data.append(row_data)

    # Convert maps to lists for frontend consumption
    return {
        "graph": {
            "nodes": list(nodes_map.values()),
            "edges": list(edges_map.values())
        },
        "table": table_data
    }
    

# 4. The Optimized Cypher Query
# We explicitly map your specific fields (reasoning, date, source_files) here.
CYPHER_QUERY = """
    MATCH (n)-[r]->(m)
    // Optional: Limit for performance if DB is huge
    LIMIT 100

    WITH n, r, m
    
    // 1. Pack Source & Target Nodes
    // We use "name" for the visual label because your insertion code uses "name" as the key.
    WITH collect(DISTINCT {
        key: elementId(n), 
        attributes: {
            // Visual Label: "Mikhail Kasyanov"
            name: n.name,
            
            // Category: "Person", "Organization" (Derived from your Entity.label)
            label: head(labels(n)) 
        }
    }) + collect(DISTINCT {
        key: elementId(m), 
        attributes: {
            name: m.name,
            label: head(labels(m))
        }
    }) as rawNodes, 
    
    // 2. Pack Edges (Relationships)
    // Mapping your specific Relationship fields here
    collect({
        key: elementId(r),
        source: elementId(n),
        target: elementId(m),
        attributes: {
            
            // --- YOUR CUSTOM DATA ---
            label: type(r),          // e.g. "HELD_POSITION"
            date: r.date,            // e.g. "2004-02-15"
            reasoning: r.reasoning,  // The explanation text
            context: r.context,      // The context (e.g., "Winter Gas Dispute")
            src: r.source_files[0],
            // Visual Logic: Thicker line if multiple source files exist
            // source_count: size(r.source_files),
            
            // Debugging info
            created_at: toString(r.created_at)
        }
    }) as edges

    // 3. Deduplicate Nodes (Because a node can be both a source and a target)
    UNWIND rawNodes as node
    WITH collect(DISTINCT node) as nodes, edges
    
    // 4. Return Single JSON Object
    RETURN { nodes: nodes, edges: edges } as graphData
"""




def get_graph_data_tx(tx):
    result = tx.run(CYPHER_QUERY)
    record = result.single()
    return record["graphData"] if record else {"nodes": [], "edges": []}


@app.post("/api/query")
def exec_query_and_parse(query: Query):
    print(f"Executing {query.query}")
    if not driver:
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    try:
        # Execute query in a read transaction (Best Practice for Clusters/Performance)
        with driver.session() as session:
            result = session.run(query.query) # type: ignore
            data = process_neo4j_results(result)
            # print(data)
            return data
        
    except Exception as e:
        print(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# output example for @app.post("/api/query")
# {
#   "graph": {
#     "nodes": [
#       {
#         "id": "4:b2708301-8eb4-46c4-b223-94e1558f39c5:280",
#         "labels": [
#           "Person"
#         ],
#         "properties": {
#           "name": "антон яковлев"
#         }
#       }
#     ],
#     "edges": []
#   },
#   "table": [
#     {
#       "u.name": "юрий яковлев",
#       "w": "Node(4:b2708301-8eb4-46c4-b223-94e1558f39c5:280)"
#     }
#   ]
# }








#return results of predefined query 
@app.get("/api/graph")
async def get_graph():
    if not driver:
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    try:
        # Execute query in a read transaction (Best Practice for Clusters/Performance)
        with driver.session() as session:
            data = session.execute_read(get_graph_data_tx)
            print(f"Loaded nodes : {len(data["nodes"])}")
            return data
    except Exception as e:
        print(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reques_query")
def get_query(query: QueryAI):
    print(f"Imagining {query.prompt}")
    try:
        return requester.generate_from_language(query.prompt, query.current_query)
    except Exception as e:
        print(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # Run with: python -m uvicorn web:app --host 127.0.0.1 --port 8000 --reload
    uvicorn.run("web:app", host="127.0.0.1", port=8000, reload=True)