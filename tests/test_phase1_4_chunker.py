"""Unit tests for Phase 1.4 Chunker."""

from __future__ import annotations

import pytest
from src.ingest.subphases.phase_1_4_chunker.chunker import Chunker


def test_chunker_splits_and_preserves_metadata():
    doc = {
        "scheme_id": "hdfc-mid-cap-fund-direct-growth",
        "source_url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        "fetched_at": "20260520T120000Z",
        "sections": [
            {
                "name": "Expense Ratio",
                "text": "NAV: 19 May '26 \u20b9219.80 Min. for SIP \u20b9100. Expense ratio 0.77%"
            },
            {
                "name": "Main Body",
                "text": " ".join(["| Row 1 Col 1 | Row 1 Col 2 | |---|---| | Val 1 | Val 2 | | Row 2 Col 1 | Row 2 Col 2 | |---|---| | Val 3 | Val 4 | | This is a very long section trailing text. Let's make sure it chunks. Here is more sentence data. And even more text to exceed the cap."] * 5)
            }
        ],
        "must_have_anchors": {},
        "extraction_health": "ok"
    }
    
    chunker = Chunker()
    chunks = list(chunker.chunk(doc))
    
    # 1. Total chunk count must match expectations
    assert len(chunks) > 1
    
    # 2. Check chunk properties
    for c in chunks:
        assert c["scheme_id"] == "hdfc-mid-cap-fund-direct-growth"
        assert c["scheme_name"] == "HDFC Mid Cap Fund Direct Growth"
        assert c["doc_type"] == "Product_Page"
        assert c["source_url"] == doc["source_url"]
        assert "chunk_id" in c
        assert "content_hash" in c
        assert "stable_content_hash" in c
        
    # 3. Check section division
    expense_chunks = [c for c in chunks if c["section"] == "Expense Ratio"]
    assert len(expense_chunks) == 1
    assert expense_chunks[0]["text"] == "NAV: 19 May '26 \u20b9219.80 Min. for SIP \u20b9100. Expense ratio 0.77%"
    
    body_chunks = [c for c in chunks if c["section"] == "Main Body"]
    assert len(body_chunks) > 1
