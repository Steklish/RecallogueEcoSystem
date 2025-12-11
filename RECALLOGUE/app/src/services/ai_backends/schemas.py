from datetime import datetime
import os
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional
from typing import Union

from app.src.config import settings


StatusType = Literal["completed", "error"]


class Query(BaseModel):
    """
    Represents a user query.
    """
    text: str = Field(description="The user's query text.")
    top_k: int = Field(5, description="The number of relevant chunks to retrieve.")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters to apply during the search.")

class IntentAnalysis(BaseModel):
    """
    Represents the intent analysis of a user query.
    """
    enhanced_query: str = Field(description="The context-enrichen, rewritten query with a lot of details.")
    
class DataBaseQueryList(BaseModel):
    sql_queries: List[str] = Field(description="The list of SQL queries to be executed on the database. Avoid using `UNION` in sql queries.")
    
    
class Task(BaseModel):
    goal : str = Field(description="Goal of the task")
    condition : str = Field(description="The condition of accomplishing the task")

class Subtask(BaseModel):
    action : str = Field(description="Action that needs to be preformed on the current step of the plan")

class TaskList(BaseModel):
    tasks : List[Task] = Field(description="List of tasks to accomplish")