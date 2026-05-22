import logging
import os
import re
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

from mf_faq.ingestion.indexer import Indexer

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self, index_dir: str = "data/index", model_name: str = "BAAI/bge-small-en-v1.5"):
        self.index_dir = index_dir
        self.model_name = model_name
        
        logger.info(f"Loading Index from {index_dir}...")
        self.indexer = Indexer(index_dir=self.index_dir)
        self.index_handle = self.indexer.load()
        
        logger.info(f"Loading embedding model: {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)
        
    def _contains_pii(self, query: str) -> bool:
        """
        Lightweight PII scanner.
        Flags potential PAN numbers, phone numbers, or email addresses.
        """
        # Email
        if re.search(r'[\w\.-]+@[\w\.-]+\.\w+', query):
            return True
        # Phone (10 digits)
        if re.search(r'\b\d{10}\b', query):
            return True
        # PAN Card (5 letters, 4 digits, 1 letter)
        if re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', query, re.IGNORECASE):
            return True
        return False

    def _rrf(self, dense_ranks: List[int], sparse_ranks: List[int], k: int = 60) -> List[int]:
        scores = {}
        for rank, chunk_idx in enumerate(dense_ranks):
            if chunk_idx not in scores:
                scores[chunk_idx] = 0.0
            scores[chunk_idx] += 1.0 / (k + rank + 1)
            
        for rank, chunk_idx in enumerate(sparse_ranks):
            if chunk_idx not in scores:
                scores[chunk_idx] = 0.0
            scores[chunk_idx] += 1.0 / (k + rank + 1)
            
        sorted_chunks = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return sorted_chunks

    def retrieve(self, query: str, scheme_id_hint: Optional[str] = None, top_k: int = 3, threshold: float = 0.4) -> Dict[str, Any]:
        """
        Retrieves the top_k chunks for a given query using Hybrid Search + Metadata Filtering.
        Returns a dict containing chunks, and enforces NO URL on PII/Not Found scenarios.
        """
        logger.info(f"Retrieving for query: '{query}' (scheme_hint: {scheme_id_hint})")
        
        # 1. PII Check
        if self._contains_pii(query):
            logger.warning("PII detected in query. Blocking retrieval and stripping URLs.")
            return {
                "refused": True,
                "reason": "PII Detected. Cannot process personal information.",
                "citation_url": None,
                "chunks": []
            }
        
        # 2. Embed Query
        query_emb = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        
        # 3. Dense Search (FAISS)
        total_chunks = len(self.index_handle.chunks)
        dense_scores, dense_indices = self.index_handle.dense.search(query_emb, total_chunks)
        dense_scores = dense_scores[0]
        dense_indices = dense_indices[0]
        
        # 4. Sparse Search (BM25)
        tokenized_query = query.lower().split()
        sparse_scores = self.index_handle.sparse.get_scores(tokenized_query)
        sparse_indices = np.argsort(sparse_scores)[::-1]
        
        # 5. Filter by scheme_id
        valid_indices = set(range(total_chunks))
        if scheme_id_hint:
            valid_indices = {i for i in range(total_chunks) if self.index_handle.chunks[i].get("scheme_id") == scheme_id_hint}
            
        filtered_dense_ranks = [idx for idx in dense_indices if idx in valid_indices]
        filtered_sparse_ranks = [idx for idx in sparse_indices if idx in valid_indices]
        
        # 6. Reciprocal Rank Fusion (RRF)
        fused_chunk_indices = self._rrf(filtered_dense_ranks, filtered_sparse_ranks)
        
        # 7. Apply Threshold and Select Top-K
        results = []
        for idx in fused_chunk_indices:
            original_dense_rank = np.where(dense_indices == idx)[0][0]
            semantic_score = dense_scores[original_dense_rank]
            
            # Thresholding Fallback
            if len(results) == 0 and semantic_score < threshold:
                logger.warning(f"Top chunk semantic score ({semantic_score:.2f}) is below threshold ({threshold}). Returning Not Found with NO URL.")
                return {
                    "refused": True,
                    "reason": "I couldn't find this information on the scheme pages.",
                    "citation_url": None, # MUST BE NONE
                    "chunks": []
                }
                
            chunk_data = self.index_handle.chunks[idx].copy()
            chunk_data["_score"] = float(semantic_score)
            results.append(chunk_data)
            
            if len(results) >= top_k:
                break
                
        return {
            "refused": False,
            "reason": None,
            "citation_url": results[0]["source_url"] if results else None,
            "chunks": results
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    retriever = Retriever()
    
    test_queries = [
        ("What is the expense ratio?", "hdfc-elss-tax-saver-fund-direct-plan-growth"),
        ("Here is my PAN ABCDE1234F, can you check my balance?", None),
        ("Tell me a completely random irrelevant fact about space.", None)
    ]
    
    for q, hint in test_queries:
        res = retriever.retrieve(q, scheme_id_hint=hint, top_k=2)
        print(f"\nQuery: {q} | Hint: {hint}")
        print(f"Refused: {res['refused']}")
        print(f"Reason: {res['reason']}")
        print(f"Attached URL: {res['citation_url']}")
        if not res['refused']:
            for i, r in enumerate(res['chunks']):
                print(f" [{i+1}] Score: {r['_score']:.2f} | Section: {r['section']} | Text: {r['text'][:60]}...")
