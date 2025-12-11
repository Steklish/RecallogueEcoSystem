import os

from pydantic import BaseModel, Field
from generator import Generator

class Query(BaseModel):
  	query : str = Field(description="Cypher query")

class QueryAI(BaseModel):
	prompt : str = Field(description="AI natural language query")
	current_query : str = Field(description="Current Cypher query (user might want to edit it)")

class Requester():
    def __init__(self, generator : Generator, labels) -> None:
        self.labels = labels
        self.generator = generator

    def generate_from_language(self, text:str, current_query: str) -> Query:
        rel_schema = """
        "type": "RELATIONSHIP_TYPE", // in UPPER_SNAKE_CASE
    	"reasoning": "string data (contains some reasoning text (useful for search))"
      """
        
        
        prompt=f"""
    You are an expert Neo4j developer and data scientist. Your task is to translate natural language questions into valid, optimized Cypher queries based strictly on the schema provided below.

	if a query is completely unrelated text, you might put an answer into query field like:
	```NOT A VALID PROMPT FOR CYHER QUERYц```

	User might want to edit the query they have currently (But not necessary).
	<current_query>
 	{current_query}
	</current_query>
 
    ### 1. GRAPH SCHEMA
    **Available Node Labels & Properties:**
    {self.labels}
    IMPORTANT nodes dont have properties and all the data stored mostly in relationships.
    EXAMPLE: a person might HOLD_POSITION of somethig, so the position name is stored in the relationship, not in the node.
    ---
    **Available Relationship attributes (example):**
    {rel_schema}
    ---
    ### 2. RULES & CONSTRAINTS
    - **all entity names are in lowercase in this database**
    - **Direction:** Pay close attention to relationship direction (e.g., `(a)-[:REL]->(b)` vs `(a)<-[:REL]-(b)`). If direction is ambiguous, use undirected relationships `(a)-[:REL]-(b)`.
    - **Case Sensitivity:** Assume string matching should be case-insensitive (e.g., use `toLower(n.name) = toLower('Value')` or `CONTAINS`) unless specified otherwise.
    - **Syntactical Correctness:** Ensure all queries are syntactically correct for the latest version of Neo4j.
    - **Output:** Do not provide explanations or conversational filler. Output ONLY the Cypher query inside a markdown code block.
    - **Use `CONTAINS` for string searches instead of exact matches.**
    - **Always set limot for data retrieved. If user doesnt asks specificly try to make it not greater that 500 entries**
    ---
    ### 4. CURRENT REQUEST
    **Natural Language Query:**
    {text}
    """
        
        query = self.generator.generate_one_shot(
            pydantic_model=Query,
            prompt=prompt
        )
        
        return query