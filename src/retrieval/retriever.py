"""Phase 3 Retrieval Engine."""

import re
import numpy as np
from typing import List, Optional, Dict
from sentence_transformers import SentenceTransformer
from src.ingest.subphases.phase_1_6_indexer.indexer import Indexer, IndexHandle
from src.retrieval.models import RetrievedChunk, RetrievalResult

class Retriever:
    def __init__(self, index_dir: str = "data/index", model_name: str = "BAAI/bge-small-en-v1.5"):
        self.index_dir = index_dir
        self.indexer = Indexer(index_dir=index_dir)
        self.handle: Optional[IndexHandle] = None
        self.embedder = SentenceTransformer(model_name)
        
    def load(self):
        """Loads the indexes into memory."""
        if not self.handle:
            self.handle = self.indexer.load()
            
    def _check_pii(self, query: str) -> bool:
        """Rudimentary PII check. In production this would use Presidio or a dedicated LLM."""
        # Check for typical PII patterns (e.g. phone numbers, SSN, PAN formats)
        # PAN card format: 5 letters, 4 digits, 1 letter
        if re.search(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", query.upper()):
            return True
        # Simple phone number check
        if re.search(r"\b\d{10}\b", query):
            return True
        # Simple email check
        if re.search(r"[\w\.-]+@[\w\.-]+\.\w+", query):
            return True
        return False
        
    def search(self, query: str, scheme_id: Optional[str] = None, top_k: int = 3, threshold: float = 0.5) -> RetrievalResult:
        """Executes Hybrid Search with Metadata Pre-filtering."""
        self.load()
        
        # 1. PII Check
        if self._check_pii(query):
            return RetrievalResult(
                query=query,
                scheme_id=scheme_id,
                chunks=[],
                status="refused_pii",
                message="I cannot process queries containing Personal Identifiable Information."
            )
            
        # 2. Metadata Pre-filtering
        valid_indices = []
        for idx, chunk in enumerate(self.handle.chunks):
            if scheme_id is None or chunk["scheme_id"] == scheme_id:
                valid_indices.append(idx)
                
        if not valid_indices:
            return RetrievalResult(
                query=query,
                scheme_id=scheme_id,
                chunks=[],
                status="not_found",
                message="I couldn't find this on the scheme pages we use"
            )
            
        valid_indices_set = set(valid_indices)
        
        # 3. Dense Search (FAISS)
        # Embed query
        q_emb = self.embedder.encode([query], normalize_embeddings=True).astype(np.float32)
        # We query more than top_k because we need to filter post-search since FAISS doesn't easily support pre-filtering natively here
        search_k = min(len(self.handle.chunks), max(50, top_k * 5))
        dense_distances, dense_indices = self.handle.dense.search(q_emb, search_k)
        
        dense_ranks: Dict[int, int] = {}
        rank = 1
        for dist, idx in zip(dense_distances[0], dense_indices[0]):
            if idx in valid_indices_set:
                dense_ranks[int(idx)] = rank
                rank += 1
                
        # 4. Sparse Search (BM25)
        tokenized_query = query.lower().split()
        bm25_scores = self.handle.sparse.get_scores(tokenized_query)
        
        # Sort sparse scores but only keep valid indices
        sparse_scored = [(idx, bm25_scores[idx]) for idx in valid_indices]
        sparse_scored.sort(key=lambda x: x[1], reverse=True)
        
        sparse_ranks: Dict[int, int] = {}
        for rank, (idx, _) in enumerate(sparse_scored, start=1):
            sparse_ranks[idx] = rank
            
        # 5. Reciprocal Rank Fusion (RRF)
        k = 60 # RRF smoothing constant
        rrf_scores: Dict[int, float] = {}
        for idx in valid_indices:
            dense_rank = dense_ranks.get(idx, 1000)
            sparse_rank = sparse_ranks.get(idx, 1000)
            rrf_score = (1.0 / (k + dense_rank)) + (1.0 / (k + sparse_rank))
            rrf_scores[idx] = rrf_score
            
        # Sort by RRF score
        sorted_indices = sorted(rrf_scores.keys(), key=lambda idx: rrf_scores[idx], reverse=True)
        
        # 6. Thresholding & Selection
        final_chunks = []
        for i, idx in enumerate(sorted_indices[:top_k]):
            # If the best match score is too low, we abort (here we use a heuristic threshold on dense distance if available)
            # FAISS inner product distance (since normalized) is between -1 and 1. Higher is better.
            # dense_distances are inner products. Let's find the max IP for the top result.
            ip_score = 0.0
            if idx in dense_indices[0]:
                pos = np.where(dense_indices[0] == idx)[0][0]
                ip_score = dense_distances[0][pos]
                
            if i == 0 and ip_score < threshold and rrf_scores[idx] < 0.01:
                return RetrievalResult(
                    query=query,
                    scheme_id=scheme_id,
                    chunks=[],
                    status="not_found",
                    message="I couldn't find this on the scheme pages we use"
                )
                
            chunk_dict = self.handle.chunks[idx]
            final_chunks.append(RetrievedChunk(
                chunk=chunk_dict,
                score=rrf_scores[idx],
                rank=i+1
            ))
            
        if not final_chunks:
             return RetrievalResult(
                query=query,
                scheme_id=scheme_id,
                chunks=[],
                status="not_found",
                message="I couldn't find this on the scheme pages we use"
            )
            
        return RetrievalResult(
            query=query,
            scheme_id=scheme_id,
            chunks=final_chunks,
            status="success"
        )
