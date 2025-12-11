from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase
import logging
from schemas import KnowledgeGraph
from entity_normalizer import EntityNameNormalizer
import sqlite3

class Neo4jGraphManager:
    def __init__(self, uri: str, auth: tuple, sqlite_db_path: str = "entities.db"):
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.logger = logging.getLogger("Neo4jManager")
        self.entity_normalizer = EntityNameNormalizer(sqlite_db_path)
        self.sqlite_db_path = sqlite_db_path
        

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

    def _build_props_str(self, props: Dict[str, Any]) -> str:
        if not props or all(v is None for v in props.values()):
            return "{}"
        entries = []
        for k, v in props.items():
            if v is not None:  # Only include properties that have values
                entries.append(f"`{k}`: {self._sanitize(v)}") # Added backticks to keys for safety
        return "{" + ", ".join(entries) + "}"

    def _build_rel_props_str(self, rel) -> str:
    # Get only public data attributes (exclude private, methods, properties)
        props_dict = {}
        for attr_name in dir(rel):
            if (attr_name.startswith('_') or           # Skip private attributes
                callable(getattr(rel, attr_name)) or   # Skip methods
                attr_name in {'__dict__', '__class__'}): # Skip special dunder attrs
                continue
                
            attr_value = getattr(rel, attr_name)
            if attr_value is not None:
                props_dict[attr_name] = attr_value
        
        if not props_dict:
            return ""
        
        # Cypher props string for parameter binding
        props_str = ", ".join(f'{k}: ${k}' for k in props_dict)
        return props_str



    def _build_entity_props_str(self, rel) -> str:
    # Get only public data attributes (exclude private, methods, properties)
        props_dict = {}
        for attr_name in dir(rel):
            if (attr_name.startswith('_') or           # Skip private attributes
                callable(getattr(rel, attr_name)) or   # Skip methods
                attr_name in {'__dict__', '__class__'}): # Skip special dunder attrs
                continue
                
            attr_value = getattr(rel, attr_name)
            if attr_value is not None:
                props_dict[attr_name] = attr_value
        
        if not props_dict:
            return ""
        
        # Cypher props string for parameter binding
        props_str = ", ".join(f'{k}: ${k}' for k in props_dict)
        return props_str

    def generate_cypher(self, graph_data: 'KnowledgeGraph', src_filename=None) -> List[str]:
        queries = []

        # --- STEP 1: Process Nodes ---
        for entity in graph_data.entities:
            safe_name = self._sanitize(entity.name)
            props_str = self._build_entity_props_str(entity)

            # Update: ON MATCH now updates properties too
            query = (
                f"MERGE (n {{name: {safe_name}}})"
                f"ON CREATE SET n:{entity.label}"
            )
            queries.append(query)

        # --- STEP 2: Process Relationships ---
        for rel in graph_data.relationships:
            source_safe = self._sanitize(rel.source)
            target_safe = self._sanitize(rel.target)

            # Build relationship properties using the new method that includes dates
            rel_props_str = self._build_rel_props_str(rel)

            # Get source_file separately for the source files list
            source_file_val = self._sanitize(src_filename) if src_filename else "null"

            # Merge on TYPE only (not properties), then accumulate evidence
            query = (
                f"MATCH (a {{name: {source_safe}}}) "
                f"MATCH (b {{name: {target_safe}}}) "
                f"MERGE (a)-[r:{rel.type}]->(b) "
                f"ON CREATE SET r += {rel_props_str}, "
                f"r.source_files = [{source_file_val}], "
                f"r.created_at = timestamp() "
                f"ON MATCH SET "
                f"r += {rel_props_str}, "
                f"r.source_files = CASE WHEN {source_file_val} IN r.source_files THEN r.source_files ELSE r.source_files + {source_file_val} END, "
                f"r.updated_at = timestamp()"
            )
            queries.append(query)

        return queries
    
    def _get_relationship_properties(self, rel) -> Dict[str, Any]:
        # Use Pydantic's built-in serialization
        if hasattr(rel, 'model_dump'):
            # Pydantic v2
            props = rel.model_dump(exclude_unset=True, exclude_none=True)
        else:
            # Pydantic v1 fallback
            props = rel.dict(exclude_unset=True, exclude_none=True)
        
        # Remove relationship structure fields
        for key in ["source", "target", "type"]:
            props.pop(key, None)
        
        return props
    
    def execute_graph(self, graph_data: 'KnowledgeGraph', src_filename: Optional[str] = None):
        processed_graph_data = self.entity_normalizer.normalize_entity_names(graph_data)

        with self.driver.session() as session:
            # --- STEP 1: Create nodes ---
            for entity in processed_graph_data.entities:
                query = """
                MERGE (n {name: $name})
                ON CREATE SET n:`%s`
                """ % entity.label

                try:
                    session.run(query, name=entity.name) # type: ignore
                    self.logger.info(f"Created/merged entity: {entity.name}")
                except Exception as e:
                    self.logger.error(f"Failed to create entity {entity.name}: {e}")

            # --- STEP 2: Create relationships ---
            for rel in processed_graph_data.relationships:
                rel_props = self._get_relationship_properties(rel)

                query = f"""
                MATCH (a {{name: $source}})
                MATCH (b {{name: $target}})
                MERGE (a)-[r:`{rel.type}`]->(b)
                ON CREATE SET 
                    r += $props,
                    r.source_files = CASE WHEN $src_file IS NULL THEN [] ELSE [$src_file] END,
                    r.created_at = timestamp()
                ON MATCH SET 
                    r += $props,
                    r.source_files = CASE 
                        WHEN $src_file IS NULL THEN r.source_files
                        WHEN $src_file IN r.source_files THEN r.source_files
                        ELSE r.source_files + $src_file
                    END,
                    r.updated_at = timestamp()
                """

                params = {
                    "source": rel.source,
                    "target": rel.target,
                    "props": rel_props,
                    "src_file": src_filename
                }

                try:
                    session.run(query, params) # type: ignore
                    self.logger.info(f"Created/merged relationship: {rel.source} -[{rel.type}]-> {rel.target}")
                except Exception as e:
                    self.logger.error(f"Failed to create relationship {rel.source} -[{rel.type}]-> {rel.target}: {e}")

    def clear_entities_db(self):
        """Clear all entities from the SQLite database using the entity normalizer."""
        self.entity_normalizer.clear_entities_db()

    def create_indexes(self):
        # Important: Run this once to make lookups fast
        query = "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS UNIQUE"
        with self.driver.session() as session:
            session.run(query)