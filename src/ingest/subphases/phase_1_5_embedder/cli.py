"""CLI entry for Phase 1.5 Embedder."""

from __future__ import annotations

import glob
import json
import os
import numpy as np

from src.ingest.subphases.phase_1_5_embedder.embedder import Embedder

def run() -> int:
    print("Starting Phase 1.5 Embedder...")
    
    # 1. Gather all chunks
    chunk_files = glob.glob("data/processed/*/chunks.jsonl")
    all_chunks = []
    for cf in chunk_files:
        with open(cf, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    all_chunks.append(json.loads(line))
                    
    if not all_chunks:
        print("No chunks found to embed.")
        return 0

    print(f"Found {len(all_chunks)} total chunks to embed.")

    try:
        # 2. Initialize Embedder
        embedder = Embedder()
        
        # 3. Generate Embeddings
        result = embedder.embed(all_chunks)
        
        # 4. Save to data/index/
        os.makedirs("data/index", exist_ok=True)
        
        # Save embeddings.npy
        emb_path = "data/index/embeddings.npy"
        np.save(emb_path, result["embeddings"])
        print(f"  - Saved embeddings to {emb_path} (shape: {result['embeddings'].shape})")
        
        # Save chunks.jsonl
        chunks_path = "data/index/chunks.jsonl"
        with open(chunks_path, "w", encoding="utf-8") as f:
            for chunk in result["chunks"]:
                f.write(json.dumps(chunk) + "\n")
        print(f"  - Saved chunks to {chunks_path}")
                
        # Save embedder.json
        embedder_metadata = {
            "model": embedder.model_name,
            "version": embedder.version,
            "dim": embedder.dim
        }
        meta_path = "data/index/embedder.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(embedder_metadata, f, indent=2)
        print(f"  - Saved metadata to {meta_path}")
            
        print(f"Embedder Complete. Successfully embedded {len(result['chunks'])} chunks.")
        return 0
    except Exception as e:
        print(f"Embedder ERROR: {e}")
        return 1
