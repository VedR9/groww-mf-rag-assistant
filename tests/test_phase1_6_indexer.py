import os
import json
import numpy as np
import pytest
from src.ingest.subphases.phase_1_6_indexer.indexer import Indexer

def test_indexer_build_and_load(tmp_path):
    # Setup mock data in a temporary index directory
    index_dir = tmp_path / "index"
    index_dir.mkdir()
    
    # 1. Mock embeddings (2 chunks, dim=3)
    dummy_embeddings = np.array([
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6]
    ], dtype=np.float32)
    np.save(index_dir / "embeddings.npy", dummy_embeddings)
    
    # 2. Mock chunks.jsonl
    chunks = [
        {"chunk_id": "c1", "scheme_id": "scheme-A", "text": "This is a test chunk", "stable_content_hash": "hash1"},
        {"chunk_id": "c2", "scheme_id": "scheme-A", "text": "Another test chunk", "stable_content_hash": "hash1"}
    ]
    with open(index_dir / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c) + "\n")
            
    # 3. Mock embedder.json
    embedder_meta = {"model": "test-model", "version": "1.0", "dim": 3}
    with open(index_dir / "embedder.json", "w", encoding="utf-8") as f:
        json.dump(embedder_meta, f)
        
    # Initialize indexer with the temp directory
    indexer = Indexer(index_dir=str(index_dir))
    
    # Execute build
    indexer.build()
    
    # Verify artifacts were moved correctly from staging to the target dir
    assert os.path.exists(index_dir / "vector.faiss")
    assert os.path.exists(index_dir / "bm25.pkl")
    assert os.path.exists(index_dir / "manifest.json")
    assert not os.path.exists(index_dir / ".staging") # Staging should be cleaned up
    
    # Verify manifest contents
    with open(index_dir / "manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    assert manifest["n_chunks"] == 2
    assert manifest["embedder"]["model"] == "test-model"
    assert manifest["per_scheme_counts"] == {"scheme-A": 2}
    
    # Execute load
    handle = indexer.load()
    
    # Verify handle structure
    assert handle.dense.ntotal == 2
    assert handle.dense.d == 3
    assert len(handle.chunks) == 2
    assert hasattr(handle.sparse, "get_scores")
