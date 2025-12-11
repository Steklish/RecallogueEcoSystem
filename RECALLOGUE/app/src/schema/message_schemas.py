from typing import Dict, List, Optional
from pydantic import BaseModel


class UserMessageRequest(BaseModel):
    content: str
    sources: Optional[List[str]]
    attachments: Optional[List[str]]
    other: Optional[Dict]
    
class SystemResponse(BaseModel):
    content: str
    sources: Optional[List[str]]
    attachments: Optional[List[str]]
    other: Optional[Dict]