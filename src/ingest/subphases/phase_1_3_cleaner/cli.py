"""CLI entry for Phase 1.3 Cleaner."""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path
from src.ingest.subphases.phase_1_3_cleaner.cleaner import Cleaner


def run() -> int:
    print("Starting Phase 1.3 Cleaner & Normalizer...")
    cleaner = Cleaner()
    processed_dirs = glob.glob("data/processed/*")
    
    success_count = 0
    failed_count = 0
    
    for pdir in processed_dirs:
        scheme_id = os.path.basename(pdir)
        ext_path = os.path.join(pdir, "extracted.json")
        if not os.path.exists(ext_path):
            continue
            
        with open(ext_path, "r", encoding="utf-8") as f:
            doc = json.load(f)
            
        try:
            cleaned = cleaner.clean(doc)
            with open(os.path.join(pdir, "cleaned.json"), "w", encoding="utf-8") as f:
                json.dump(cleaned, f, indent=2)
                
            success_count += 1
            print(f"  - {scheme_id}: cleaned {len(cleaned['sections'])} sections successfully")
        except Exception as e:
            print(f"  - {scheme_id}: ERROR: {e}")
            failed_count += 1
            
    print(f"Cleaning Complete. ok: {success_count}, failed: {failed_count}")
    return 0 if failed_count == 0 else 1
