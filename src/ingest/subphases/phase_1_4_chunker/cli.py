"""CLI entry for Phase 1.4 Chunker."""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path
from src.foundation.allowlist import CLOSED_CORPUS_URLS
from src.ingest.subphases.phase_1_4_chunker.chunker import Chunker


def run() -> int:
    print("Starting Phase 1.4 Chunker...")
    chunker = Chunker()
    processed_dirs = glob.glob("data/processed/*")
    
    success_count = 0
    failed_count = 0
    total_chunks_emitted = 0
    
    for pdir in processed_dirs:
        if not os.path.isdir(pdir):
            continue
            
        scheme_id = os.path.basename(pdir)
        cleaned_path = os.path.join(pdir, "cleaned.json")
        if not os.path.exists(cleaned_path):
            continue
            
        with open(cleaned_path, "r", encoding="utf-8") as f:
            doc = json.load(f)
            
        try:
            chunks = list(chunker.chunk(doc))
            
            # Validation criteria as per docs/architecture.md Phase 1.4 Chunker
            valid = True
            errors = []
            
            # 1. Total chunk count band checking: 5 <= n <= 20 per scheme
            n = len(chunks)
            if not (5 <= n <= 20):
                errors.append(f"Chunk count {n} out of expected band [5, 20]")
                valid = False
                
            cleaned_sections = {s["name"] for s in doc.get("sections", []) if len(s["text"].split()) >= 5}
            chunk_sections = set()
            
            for c in chunks:
                # 2. Check source_url in whitelist
                if c["source_url"] not in CLOSED_CORPUS_URLS:
                    errors.append(f"Chunk source_url {c['source_url']!r} not in whitelisted corpus")
                    valid = False
                    
                # 3. Check section is drawn from cleaned doc's sections set
                if c["section"] not in cleaned_sections:
                    errors.append(f"Chunk section {c['section']!r} not found in cleaned sections list")
                    valid = False
                    
                chunk_sections.add(c["section"])
                
            # 4. Check coverage: union of chunks covers every section >= 5 tokens
            missing_sections = cleaned_sections - chunk_sections
            if missing_sections:
                errors.append(f"Not all sections covered by chunks. Missing: {sorted(missing_sections)}")
                valid = False
                
            if not valid:
                print(f"  - {scheme_id}: VALIDATION FAILED:")
                for err in errors:
                    print(f"      * {err}")
                failed_count += 1
            else:
                chunks_path = os.path.join(pdir, "chunks.jsonl")
                with open(chunks_path, "w", encoding="utf-8") as f:
                    for c in chunks:
                        f.write(json.dumps(c) + "\n")
                success_count += 1
                total_chunks_emitted += n
                print(f"  - {scheme_id}: chunked {n} chunks successfully")
        except Exception as e:
            print(f"  - {scheme_id}: ERROR: {e}")
            failed_count += 1
            
    print(f"Chunking Complete. ok: {success_count}, failed: {failed_count}, total chunks: {total_chunks_emitted}")
    return 0 if failed_count == 0 else 1
