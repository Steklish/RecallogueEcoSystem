from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# (Include the MessageRole Enum from above here)
class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# 1. Base Model: Shared properties
# --------------------------------
# Contains fields provided during creation.
class ChatMessageBase(BaseModel):
    thread_id: int
    role: MessageRole
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    links: Optional[List[Dict[str, Any]]] = None
    message_metadata: Optional[Dict[str, Any]] = None

    # Allow a different name in the API ('metadata') than in the code ('message_metadata')
    class Config:
        populate_by_name = True


# 2. Create Model: Properties to receive on item creation
# -------------------------------------------------------
# This model defines the exact fields required to create a new message.
# It inherits everything from the Base model.
class ChatMessageCreate(ChatMessageBase):
    pass


# 3. Update Model: Properties to receive on item update
# -----------------------------------------------------
# Used for PATCH requests. All fields are optional.
# It's generally not recommended to allow updating thread_id or role.
class ChatMessageUpdate(BaseModel):
    content: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    links: Optional[List[Dict[str, Any]]] = None
    message_metadata: Optional[Dict[str, Any]] = Field(None, alias='metadata')


# 4. Read Model: Properties to return to the client
# -------------------------------------------------
# This is the full representation of the object as it exists in the database,
# including all the auto-generated fields like id and timestamps.
class ChatMessage(ChatMessageBase):
    id: int
    timestamp: datetime
    created_at: datetime

    # This configuration allows Pydantic to create the model
    # from an arbitrary ORM object (like your SQLAlchemy ChatMessage instance).
    class Config:
        from_attributes = True
        # For Pydantic v1, you would use:
        # orm_mode = True