import json
import logging
import os
import glob
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class Embedder:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self.version = "1.5"
        self.dim = 384
        
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)

    def embed(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Embeds a list of chunks.
        Prepends scheme_name to text to separate identical boilerplate across schemes.
        """
        texts = []
        for chunk in chunks:
            scheme_name = chunk.get("scheme_name", "")
            text = chunk.get("text", "")
            full_text = f"{scheme_name}\n\n{text}"
            texts.append(full_text)

        logger.info(f"Embedding {len(texts)} chunks...")
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        
        return {
            "embeddings": embeddings,
            "chunks": chunks
        }


if __name__ == "__main__":
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
        exit(0)

    # 2. Initialize Embedder
    embedder = Embedder()
    
    # 3. Generate Embeddings
    result = embedder.embed(all_chunks)
    
    # 4. Save to data/index/
    os.makedirs("data/index", exist_ok=True)
    
    # Save embeddings.npy
    np.save("data/index/embeddings.npy", result["embeddings"])
    
    # Save chunks.jsonl
    with open("data/index/chunks.jsonl", "w", encoding="utf-8") as f:
        for chunk in result["chunks"]:
            f.write(json.dumps(chunk) + "\n")
            
    # Save embedder.json
    embedder_metadata = {
        "model": embedder.model_name,
        "version": embedder.version,
        "dim": embedder.dim
    }
    with open("data/index/embedder.json", "w", encoding="utf-8") as f:
        json.dump(embedder_metadata, f, indent=2)
        
    print(f"Successfully embedded {len(result['chunks'])} chunks.")

