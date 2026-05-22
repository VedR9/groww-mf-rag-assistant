"""CLI entry for Phase 1.7 Refresh & Health."""

from __future__ import annotations

import sys
from src.ingest.subphases.phase_1_7_refresh.pipeline import Pipeline

def run() -> int:
    dry_run = "--dry-run" in sys.argv
    skip_fetch = "--skip-fetch" in sys.argv
    force = "--force" in sys.argv
    
    print(f"Starting Phase 1.7 Pipeline Orchestrator (dry_run={dry_run}, skip_fetch={skip_fetch}, force={force})...")
    
    pipeline = Pipeline()
    success = pipeline.refresh(force=force, dry_run=dry_run, skip_fetch=skip_fetch)
    
    if success:
        print("Pipeline Orchestrator Complete: SUCCESS")
        return 0
    else:
        print("Pipeline Orchestrator Complete: FAILED")
        return 1
