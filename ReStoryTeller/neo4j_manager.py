from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase
import logging
from schemas import AIKnowledgeGraph

class Neo4jGraphManager:
    def __init__(self, uri: str, auth: tuple):
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.logger = logging.getLogger("Neo4jManager")  

    def close(self):
        self.driver.close()

    def _sanitize(self, val: Any) -> str:
        if isinstance(val, str):
            safe_str = val.replace("'", "\\'")
            safe_str.lower()
            return f"'{safe_str}'"
        elif isinstance(val, bool):
            return "true" if val else "false"
        elif val is None:
            return "null"
        else:
            return str(val)

    def create_indexes(self):
        # Important: Run this once to make lookups fast
        query = "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS UNIQUE"
        with self.driver.session() as session:
            session.run(query)