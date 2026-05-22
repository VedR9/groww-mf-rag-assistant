"""CLI entry for Phase 1.2 Extractor."""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path
from src.ingest.subphases.phase_1_2_extractor.extractor import Extractor


def run() -> int:
    print("Starting Phase 1.2 Extractor...")
    extractor = Extractor()
    raw_dirs = glob.glob("data/raw/*")
    
    success_count = 0
    degraded_count = 0
    failed_count = 0
    
    for raw_dir in raw_dirs:
        scheme_id = os.path.basename(raw_dir)
        meta_path = os.path.join(raw_dir, "meta.json")
        if not os.path.exists(meta_path):
            continue
            
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            
        html_files = glob.glob(os.path.join(raw_dir, "*.html"))
        if not html_files:
            continue
            
        html_files.sort()
        html_file = html_files[-1]
        
        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()
            
        try:
            extracted = extractor.extract(html, scheme_id, meta["url"], meta["fetched_at"])
            out_dir = Path("data/processed") / scheme_id
            out_dir.mkdir(parents=True, exist_ok=True)
            
            with open(out_dir / "extracted.json", "w", encoding="utf-8") as f:
                json.dump(extracted, f, indent=2)
                
            health = extracted["extraction_health"]
            if health == "ok":
                success_count += 1
            else:
                degraded_count += 1
            print(f"  - {scheme_id}: extraction_health={health}")
        except Exception as e:
            print(f"  - {scheme_id}: ERROR: {e}")
            failed_count += 1
            
    print(f"Extraction Complete. ok: {success_count}, degraded: {degraded_count}, failed: {failed_count}")
    return 0 if failed_count == 0 else 1
