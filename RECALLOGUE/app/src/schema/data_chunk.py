from pydantic import BaseModel, Field

class DataChunk(BaseModel):
    content : str = Field(description="Chunk content")
    metadata : dict = Field(description="Any additional chunk data")
    document : str = Field(description="Original document name.")
    document_total : int = Field(description="Total chunks in the original document")
    number : int = Field(description="Chunk number inside the original document")
    