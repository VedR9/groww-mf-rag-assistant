"""Data models for Phase 3 Retrieval."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class RetrievedChunk:
    """A chunk retrieved from the index with its relevance score."""
    chunk: Dict[str, Any]
    score: float
    rank: int

@dataclass
class RetrievalResult:
    """The final result object returned by the retriever."""
    query: str
    scheme_id: Optional[str]
    chunks: List[RetrievedChunk]
    status: str  # "success", "refused_pii", "not_found"
    message: Optional[str] = None
