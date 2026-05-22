"""Unit tests for Phase 1.2 Extractor."""

from __future__ import annotations

import pytest
from src.ingest.subphases.phase_1_2_extractor.extractor import Extractor


def test_extractor_extracts_sections_and_anchors():
    html = """
    <html>
        <body>
            <h2>Expense Ratio</h2>
            <div>This is the expense ratio of the fund which is 0.77%.</div>
            
            <h2>Exit Load</h2>
            <div>An exit load of 1% applies for redemptions within 1 year.</div>
            
            <h2>Benchmark</h2>
            <div>The fund is benchmarked against NIFTY 50.</div>
            
            <h2>FAQs</h2>
            <div>Frequently Asked Questions are here.</div>
            
            <table>
                <tr>
                    <td>Min SIP</td>
                    <td>₹100</td>
                </tr>
            </table>
            
            <svg aria-label="high riskometer level">
                <path d="M10 10"/>
            </svg>
        </body>
    </html>
    """
    
    extractor = Extractor()
    res = extractor.extract(html, "hdfc-mid-cap", "https://groww.in/test", "20260520T120000Z")
    
    assert res["scheme_id"] == "hdfc-mid-cap"
    assert res["source_url"] == "https://groww.in/test"
    assert res["fetched_at"] == "20260520T120000Z"
    
    sections = {s["name"]: s["text"] for s in res["sections"]}
    assert "Expense Ratio" in sections
    assert "Exit Load" in sections
    assert "Benchmark" in sections
    assert "FAQs" in sections
    assert "Riskometer" in sections
    assert "Fund Details" in sections
    
    assert res["must_have_anchors"]["Expense Ratio"] is True
    assert res["must_have_anchors"]["Exit Load"] is True
    assert res["must_have_anchors"]["Benchmark"] is True
    assert res["must_have_anchors"]["Riskometer"] is True
    assert res["extraction_health"] == "ok"


def test_extractor_degraded_health_when_anchors_missing():
    html = """
    <html>
        <body>
            <h2>Only One Header</h2>
            <div>Nothing else.</div>
        </body>
    </html>
    """
    
    extractor = Extractor()
    res = extractor.extract(html, "hdfc-mid-cap", "https://groww.in/test", "20260520T120000Z")
    
    # sum of anchors_found < 4 -> degraded
    assert res["extraction_health"] == "degraded"
