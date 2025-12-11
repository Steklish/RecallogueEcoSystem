from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class Entity(BaseModel):
    name: str = Field(description="Unique identifier (e.g., 'Mikhail Kasyanov', 'Prime Minister').")
    label: str = Field(description="Type: Person, Organization, Role, Country, Event.")
    # Specific fields for entity properties
    description: Optional[str] = Field(default=None, description="Time independant context of the entity (e.g., 'political background').")
    # Note: Descriptions should not  be stored in graph entities

class Relationship(BaseModel):
    source: str = Field(description="Name of the source entity.")
    target: str = Field(description="Name of the target entity.")
    type: str = Field(description="Relationship type (e.g., HELD_POSITION, LOCATED_IN).")

    # Specific fields for relationship properties
    reasoning: str = Field(default="No context provided", description="Brief explanation of why this relationship exists.")
    context: str = Field(default="No context provided", description="Context of the relationship (e.g., 'Winter Gas Dispute').")

    # Temporal properties - store dates in relationships, not entities
    date: str = Field(description="Specific date of the relationship (e.g., '2004-02-15')")

class KnowledgeGraph(BaseModel):
    entities: List[Entity]
    relationships: List[Relationship]
