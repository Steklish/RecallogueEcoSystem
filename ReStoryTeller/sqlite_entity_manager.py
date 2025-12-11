import sqlite3
import os
from typing import List, Optional, Tuple
from logger_config import get_logger

logger = get_logger(__name__)


class SQLiteEntityManager:
    """
    A class to manage a SQLite table for entities with name and description fields.
    """

    def __init__(self, db_path: str = "entities.db"):
        """
        Initialize the SQLiteEntityManager.

        :param db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self.connection = None
        self._ensure_connection()
        self._create_table()

    def _ensure_connection(self):
        """Ensure a connection to the database exists."""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
        return self.connection

    def _create_table(self):
        """Create the entities table if it doesn't exist."""
        conn = self._ensure_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            )
        """)
        
        conn.commit()
        logger.info("Entities table created or verified.")

    def insert_entity(self, name: str, description: str) -> bool:
        """
        Insert a new entity into the table.

        :param name: Name of the entity.
        :param description: Description of the entity.
        :return: True if insertion was successful, False otherwise.
        """
        conn = self._ensure_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO entities (name, description) VALUES (?, ?)",
                (name, description)
            )
            conn.commit()
            logger.debug("Inserted entity: %s", name)
            return True
        except sqlite3.IntegrityError as e:
            logger.error("Entity with name '%s' already exists: %s", name, e)
            return False
        except sqlite3.Error as e:
            logger.error("Database error when inserting entity: %s", e)
            return False

    def get_entity(self, name: str) -> Optional[Tuple[int, str, str]]:
        """
        Retrieve an entity by name.

        :param name: Name of the entity to retrieve.
        :return: Entity tuple (id, name, description) if found, None otherwise.
        """
        conn = self._ensure_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name, description FROM entities WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()

        if row:
            logger.debug("Retrieved entity: %s", name)
            return tuple(row)
        else:
            logger.debug("Entity not found: %s", name)
            return None

    def get_all_entities(self) -> List[Tuple[int, str, str]]:
        """
        Retrieve all entities from the table.

        :return: List of entity tuples (id, name, description).
        """
        conn = self._ensure_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, description FROM entities ORDER BY name")
        rows = cursor.fetchall()

        logger.debug("Retrieved %d entities", len(rows))
        return [tuple(row) for row in rows]

    def update_entity(self, name: str, new_description: Optional[str] = None, new_name: Optional[str] = None) -> bool:
        """
        Update an existing entity's name and/or description.

        :param name: Current name of the entity to update.
        :param new_description: New description for the entity (optional).
        :param new_name: New name for the entity (optional).
        :return: True if update was successful, False otherwise.
        """
        conn = self._ensure_connection()
        cursor = conn.cursor()

        # Get current entity to check if it exists and to use current values if not updating
        current_entity = self.get_entity(name)
        if not current_entity:
            logger.warning("Cannot update entity: '%s' does not exist", name)
            return False

        # Determine new values
        updated_name = new_name if new_name is not None else current_entity[1]
        updated_description = new_description if new_description is not None else current_entity[2]

        try:
            cursor.execute(
                "UPDATE entities SET name = ?, description = ? WHERE name = ?",
                (updated_name, updated_description, name)
            )
            conn.commit()

            if cursor.rowcount > 0:
                logger.debug("Updated entity: %s -> %s", name, updated_name)
                return True
            else:
                logger.warning("No rows were updated for entity: %s", name)
                return False
        except sqlite3.IntegrityError as e:
            logger.error("Update failed, conflict with existing entity: %s", e)
            return False
        except sqlite3.Error as e:
            logger.error("Database error when updating entity: %s", e)
            return False

    def delete_entity(self, name: str) -> bool:
        """
        Delete an entity by name.

        :param name: Name of the entity to delete.
        :return: True if deletion was successful, False otherwise.
        """
        conn = self._ensure_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM entities WHERE name = ?", (name,))
        conn.commit()

        if cursor.rowcount > 0:
            logger.debug("Deleted entity: %s", name)
            return True
        else:
            logger.warning("No entity found to delete with name: %s", name)
            return False

    def close_connection(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed.")

    def __del__(self):
        """Cleanup method to close the connection when object is deleted."""
        self.close_connection()


# Example usage
if __name__ == "__main__":
    # Create an instance of the manager
    entity_manager = SQLiteEntityManager()

    # Insert some entities
    entity_manager.insert_entity("Python", "A high-level programming language")
    entity_manager.insert_entity("SQLite", "A lightweight disk-based database")
    entity_manager.insert_entity("Machine Learning", "AI technique using algorithms to learn patterns")

    # Retrieve an entity
    python_info = entity_manager.get_entity("Python")
    if python_info:
        id, name, description = python_info
        print(f"ID: {id}, Name: {name}, Description: {description}")

    # Get all entities
    all_entities = entity_manager.get_all_entities()
    print("\nAll entities:")
    for entity in all_entities:
        print(f"ID: {entity[0]}, Name: {entity[1]}, Description: {entity[2]}")

    # Update an entity
    entity_manager.update_entity("Python", new_description="A popular high-level programming language with dynamic semantics")

    # Retrieve updated entity
    updated_python = entity_manager.get_entity("Python")
    if updated_python:
        print(f"\nUpdated Python: {updated_python[2]}")

    # Delete an entity
    entity_manager.delete_entity("SQLite")