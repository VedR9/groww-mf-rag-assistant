from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    citation_url: Optional[str] = None
    footer: Optional[str] = None
    refused: bool = False
