import sqlite3
import os
from difflib import SequenceMatcher
import logging
from typing import Optional, Set
from schemas import KnowledgeGraph


class EntityNameNormalizer:
    """Handles entity name normalization, fuzzy matching, and storage in SQLite."""
    
    def __init__(self, sqlite_db_path: str = "entities.db"):
        self.sqlite_db_path = sqlite_db_path
        self.logger = logging.getLogger("EntityNameNormalizer")
        self.entity_cache: Set[str] = set()
        self.init_sqlite_db()
        self.load_cache()

    def init_sqlite_db(self):
        """Initialize the SQLite database and create the entities table if it doesn't exist."""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        
        # Create table to store only normalized entity names for matching
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def load_cache(self):
        """Load all normalized entity names into memory."""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM entities")
        rows = cursor.fetchall()
        self.entity_cache = {row[0] for row in rows}
        conn.close()
        self.logger.info(f"Loaded {len(self.entity_cache)} entities into cache.")

    def normalize_name(self, name: str) -> str:
        """Convert entity name to lowercase for consistent comparison."""
        return name.lower().strip()

    def _is_subset_match(self, name1: str, name2: str) -> bool:
        """
        Check if one name is a significant subset of the other.
        Example: 'lukashenko' in 'alexander lukashenko' -> True
        """
        # Split into tokens
        tokens1 = set(name1.split())
        tokens2 = set(name2.split())
        
        # If one token set is a subset of the other
        if tokens1.issubset(tokens2) or tokens2.issubset(tokens1):
            # Length check to avoid matching "the" to "the beatles" if "the" was an entity
            shorter = name1 if len(name1) < len(name2) else name2
            if len(shorter) > 3: # Arbitrary min length for a valid entity name
                return True
        return False

    def get_similar_entity(self, name: str, threshold: float = 0.8) -> str:
        """Use fuzzy matching to find similar entity names using in-memory cache."""
        normalized_name = self.normalize_name(name)
        
        # 1. Exact match check (fast)
        if normalized_name in self.entity_cache:
            return normalized_name
        
        best_match = None
        best_ratio = 0
        
        for stored_name in self.entity_cache:
            # 2. Token Subset Match (Strong Signal)
            # If "Putina" matches "Vladimira Putina", we want to merge.
            # But be careful: "Ministry of Health" vs "Ministry of Education" share tokens but are different.
            # So strict subset is safer: {Lukashenko} is subset of {Alexander, Lukashenko}
            
            is_subset = self._is_subset_match(normalized_name, stored_name)
            
            if is_subset:
                 # If it's a subset, we treat it as a very high match, but maybe not 100% automatic?
                 # Actually for typical news names (surname vs full name), this is desired.
                 # We prioritize the LONGER name usually as the canonical one, but here we return the STORED one.
                 # If we have "lukashenko" stored and input is "alexander lukashenko",
                 # stored is subset of input. We return stored ("lukashenko") -> mapping "alexander..." to "lukashenko".
                 # Ideally we want the longest one to be the key, but that requires DB migration.
                 # For now, let's just say they match.
                 return stored_name

            # 3. Standard SequenceMatcher (Fuzzy)
            ratio = SequenceMatcher(None, normalized_name, stored_name).ratio()
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = stored_name
        
        return best_match # type: ignore

    def add_entity_to_db(self, name: str, description: Optional[str] = None):
        """Add a normalized (lowercase) entity name to the SQLite database."""
        # Note: description is now ignored as it should be stored in a separate glossary
        normalized_name = self.normalize_name(name)

        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()

        try:
            # Use INSERT OR IGNORE to handle duplicates - only store name now
            if description:
                cursor.execute(
                    "INSERT OR IGNORE INTO entities (name, description) VALUES (?, ?)",
                    (normalized_name, description)
                )
            else:
                cursor.execute(
                    "INSERT OR IGNORE INTO entities (name) VALUES (?)",
                    (normalized_name,)
                )

            conn.commit()

            # Add to cache if it's not already there
            if normalized_name not in self.entity_cache:
                self.entity_cache.add(normalized_name)
        except Exception as e:
            self.logger.error(f"Error adding entity to DB: {e}")
        finally:
            conn.close()

    def get_relevant_context(self, names: list[str], threshold: float = 0.8) -> list[dict]:
        """
        Search for entities in the DB that match the provided names with similarity scoring.
        Returns matched entities with their descriptions for use in LLM prompts.
        Returns a list of dicts: [{'original_name': '...', 'matched_name': '...', 'description': '...'}, ...]
        """
        if not names:
            return []

        results = []
        normalized_inputs = {name: self.normalize_name(name) for name in names}

        for input_name, norm_input in normalized_inputs.items():
            best_match = self.get_similar_entity(input_name, threshold)

            if best_match:
                # Retrieve description for the matched entity from DB
                conn = sqlite3.connect(self.sqlite_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT description FROM entities WHERE name = ?", (best_match,))
                row = cursor.fetchone()
                description = row[0] if row and row[0] else None
                conn.close()

                results.append({
                    "original_name": input_name,
                    "matched_name": best_match,
                    "description": description
                })

        return results

    def normalize_entity_names(self, graph_data) -> KnowledgeGraph:
        """Normalize entity names (to lowercase) and use fuzzy matching to merge similar entities."""
        name_mapping = {}

        # Process all entities in the graph data
        for entity in graph_data.entities:
            # Check if there's a similar name already in the database
            similar_name = self.get_similar_entity(entity.name)

            if similar_name:
                name_mapping[entity.name] = similar_name
                self.logger.info(f"Merged entity '{entity.name}' with existing entity '{similar_name}'")
                # Add description if it exists and is not already in DB
                if entity.description:
                    self.add_entity_description(similar_name, entity.description)
            else:
                normalized_name = self.normalize_name(entity.name)
                # Add entity with its description to the database
                self.add_entity_to_db(entity.name, entity.description)
                name_mapping[entity.name] = normalized_name

        # Update entity names based on the mapping
        for entity in graph_data.entities:
            if entity.name in name_mapping:
                entity.name = name_mapping[entity.name]

        # Update relationship source and target names based on the mapping
        for rel in graph_data.relationships:
            if rel.source in name_mapping:
                rel.source = name_mapping[rel.source]
            if rel.target in name_mapping:
                rel.target = name_mapping[rel.target]

        return graph_data

    def add_entity_description(self, name: str, description: str):
        """
        Add description to an entity in the database only if it doesn't have one already.
        """
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()

        try:
            # Check if the entity already has a description
            cursor.execute("SELECT description FROM entities WHERE name = ?", (self.normalize_name(name),))
            row = cursor.fetchone()

            if row is None or row[0] is None:
                # Only update if the description is currently NULL or doesn't exist
                cursor.execute(
                    "UPDATE entities SET description = ? WHERE name = ? AND (description IS NULL OR description = '')",
                    (description, self.normalize_name(name))
                )
                conn.commit()
                self.logger.info(f"Added description for entity '{name}'")
            else:
                self.logger.info(f"Entity '{name}' already has a description, skipping update")
        except Exception as e:
            self.logger.error(f"Error adding description to entity: {e}")
        finally:
            conn.close()

    def clear_entities_db(self):
        """Clear all entities from the SQLite database."""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM entities")
        conn.commit()
        conn.close()
        self.entity_cache.clear()

        self.logger.info("Cleared all entities from the database")