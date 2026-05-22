"""CLI entry for Phase 1.6 Indexer."""

from __future__ import annotations

import logging
from src.ingest.subphases.phase_1_6_indexer.indexer import Indexer

def run() -> int:
    print("Starting Phase 1.6 Indexer...")
    
    # Configure logging so indexer info is visible
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    
    try:
        indexer = Indexer()
        indexer.build()
        print("Indexer Complete.")
        return 0
    except Exception as e:
        print(f"Indexer ERROR: {e}")
        return 1
