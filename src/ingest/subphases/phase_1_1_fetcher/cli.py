"""CLI entry for Phase 1.1 fetcher."""

from __future__ import annotations

from src.ingest.subphases.phase_1_1_fetcher.fetcher import Fetcher


def run() -> int:
    fetcher = Fetcher()
    print("Starting Phase 1.1 Crawl Fetcher...")
    results = fetcher.fetch_all()
    if not results:
        print("Crawl Fetcher failed or was aborted.")
        return 1
        
    health = "ok" if all(r.status in ("ok", "skipped") for r in results) else "degraded"
    print(f"Crawl Ingestion Complete. Health Status: {health}")
    for r in results:
        print(f"  - {r.scheme_id}: {r.status} ({r.fetcher_kind}), HTTP {r.http_status}")
        
    return 0 if health == "ok" else 1
