import json
import logging
import os
import shutil
import pickle
from datetime import datetime, timezone
from typing import Dict, Any, List
from collections import Counter
import faiss
import numpy as np
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

class IndexHandle:
    def __init__(self, dense_index, sparse_index, chunks, manifest):
        self.dense = dense_index
        self.sparse = sparse_index
        self.chunks = chunks
        self.manifest = manifest

class Indexer:
    def __init__(self, index_dir: str = "data/index"):
        self.index_dir = index_dir
        self.staging_dir = os.path.join(index_dir, ".staging")

    def build(self) -> None:
        logger.info("Building indexes in staging directory...")
        os.makedirs(self.staging_dir, exist_ok=True)
        
        embeddings_path = os.path.join(self.index_dir, "embeddings.npy")
        chunks_path = os.path.join(self.index_dir, "chunks.jsonl")
        embedder_path = os.path.join(self.index_dir, "embedder.json")
        
        if not os.path.exists(embeddings_path) or not os.path.exists(chunks_path):
            raise FileNotFoundError("Missing embeddings.npy or chunks.jsonl from Phase 1.5")
            
        embeddings = np.load(embeddings_path)
        
        chunks = []
        with open(chunks_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    chunks.append(json.loads(line))
                    
        with open(embedder_path, "r", encoding="utf-8") as f:
            embedder_meta = json.load(f)
            
        dim = embeddings.shape[1]
        dense_index = faiss.IndexFlatIP(dim) 
        dense_index.add(embeddings)
        faiss.write_index(dense_index, os.path.join(self.staging_dir, "vector.faiss"))
        
        tokenized_corpus = [chunk["text"].lower().split() for chunk in chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        with open(os.path.join(self.staging_dir, "bm25.pkl"), "wb") as f:
            pickle.dump(bm25, f)
            
        shutil.copy2(chunks_path, os.path.join(self.staging_dir, "chunks.jsonl"))
        shutil.copy2(embedder_path, os.path.join(self.staging_dir, "embedder.json"))
        
        scheme_counts = dict(Counter([c.get("scheme_id") for c in chunks]))
        source_hashes = {}
        for c in chunks:
            sid = c["scheme_id"]
            if sid not in source_hashes:
                source_hashes[sid] = c.get("stable_content_hash")
        
        manifest = {
            "built_at": datetime.now(timezone.utc).isoformat(),
            "embedder": embedder_meta,
            "n_chunks": len(chunks),
            "per_scheme_counts": scheme_counts,
            "source_hashes": source_hashes
        }
        
        with open(os.path.join(self.staging_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            
        logger.info("Performing atomic swap of staging to production index...")
        for filename in ["vector.faiss", "bm25.pkl", "chunks.jsonl", "embedder.json", "manifest.json"]:
            src = os.path.join(self.staging_dir, filename)
            dst = os.path.join(self.index_dir, filename)
            shutil.move(src, dst)
            
        shutil.rmtree(self.staging_dir)
        logger.info(f"Index built successfully. {len(chunks)} chunks indexed.")

    def load(self) -> IndexHandle:
        logger.info("Loading indexes...")
        dense_index = faiss.read_index(os.path.join(self.index_dir, "vector.faiss"))
        
        with open(os.path.join(self.index_dir, "bm25.pkl"), "rb") as f:
            sparse_index = pickle.load(f)
            
        chunks = []
        with open(os.path.join(self.index_dir, "chunks.jsonl"), "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    chunks.append(json.loads(line))
                    
        with open(os.path.join(self.index_dir, "manifest.json"), "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        logger.info(f"Loaded index with {len(chunks)} chunks.")
        return IndexHandle(dense_index, sparse_index, chunks, manifest)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    indexer = Indexer()
    indexer.build()

