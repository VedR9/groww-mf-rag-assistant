import pytest
import os
import json
import numpy as np
from src.retrieval.retriever import Retriever

def test_retriever_pii_check():
    retriever = Retriever()
    
    # Check valid query
    assert retriever._check_pii("What is the expense ratio?") == False
    
    # Check SSN/PAN format (5 letters, 4 digits, 1 letter)
    assert retriever._check_pii("Is my PAN ABCDE1234F valid?") == True
    
    # Check phone number
    assert retriever._check_pii("Call me at 9876543210") == True
    
    # Check email
    assert retriever._check_pii("Email test@example.com") == True

def test_retrieval_flow(tmp_path):
    index_dir = tmp_path / "index"
    index_dir.mkdir()
    
    # 1. Mock embeddings (3 chunks, dim=384 for bge-small)
    dim = 384
    dummy_embeddings = np.random.rand(3, dim).astype(np.float32)
    np.save(index_dir / "embeddings.npy", dummy_embeddings)
    
    # 2. Mock chunks.jsonl
    chunks = [
        {"chunk_id": "c1", "scheme_id": "scheme-A", "text": "HDFC Mid Cap expense ratio is 0.77%", "stable_content_hash": "hash1", "source_url": "url1", "document_type": "factsheet", "amc": "HDFC", "scheme_name": "HDFC Mid Cap", "section_title": "Expense Ratio", "fetched_at": "date"},
        {"chunk_id": "c2", "scheme_id": "scheme-A", "text": "HDFC Mid Cap NAV is 120.50", "stable_content_hash": "hash2", "source_url": "url1", "document_type": "factsheet", "amc": "HDFC", "scheme_name": "HDFC Mid Cap", "section_title": "NAV", "fetched_at": "date"},
        {"chunk_id": "c3", "scheme_id": "scheme-B", "text": "HDFC Large Cap NAV is 55.20", "stable_content_hash": "hash3", "source_url": "url2", "document_type": "factsheet", "amc": "HDFC", "scheme_name": "HDFC Large Cap", "section_title": "NAV", "fetched_at": "date"}
    ]
    with open(index_dir / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c) + "\n")
            
    # 3. Mock embedder.json
    embedder_meta = {"model": "BAAI/bge-small-en-v1.5", "version": "1.5", "dim": dim}
    with open(index_dir / "embedder.json", "w", encoding="utf-8") as f:
        json.dump(embedder_meta, f)
        
    # Generate FAISS and BM25 using Indexer
    from src.ingest.subphases.phase_1_6_indexer.indexer import Indexer
    indexer = Indexer(index_dir=str(index_dir))
    indexer.build()
    
    # Now run Retriever against this index
    retriever = Retriever(index_dir=str(index_dir))
    
    # Test 1: PII query
    res = retriever.search("My PAN is ABCDE1234F")
    assert res.status == "refused_pii"
    assert len(res.chunks) == 0
    assert "Personal Identifiable Information" in res.message
    
    # Test 2: Metadata filtering
    # Searching for "NAV" should theoretically hit c2 and c3. But if we filter by scheme-B, it MUST only return c3.
    res = retriever.search("What is the NAV?", scheme_id="scheme-B")
    assert res.status == "success"
    assert len(res.chunks) == 1  # Only 1 chunk in scheme-B
    assert res.chunks[0].chunk["chunk_id"] == "c3"
    
    # Test 3: Standard hybrid query
    res = retriever.search("expense ratio 0.77%")
    assert res.status == "success"
    assert len(res.chunks) > 0
    returned_ids = [c.chunk["chunk_id"] for c in res.chunks]
    assert "c1" in returned_ids  # Lexical match on 0.77% should ensure c1 is retrieved
