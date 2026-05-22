"""Unit tests for Phase 1.3 Cleaner."""

from __future__ import annotations

import pytest
from src.ingest.subphases.phase_1_3_cleaner.cleaner import Cleaner


def test_cleaner_drops_faqs_and_sanitizes():
    doc = {
        "scheme_id": "hdfc-mid-cap",
        "source_url": "https://groww.in/test",
        "fetched_at": "20260520T120000Z",
        "sections": [
            {
                "name": "Expense Ratio",
                "text": "The Expense Ratio is Rs 0.77% and also Rs. 0.8% or INR 0.77. Read all scheme related documents carefully"
            },
            {
                "name": "FAQs",
                "text": "How do I invest in this fund? You can do so easily."
            },
            {
                "name": "Fund Manager",
                "text": "Chirag Setalvad is the manager. He has 10 years of experience. His bio here."
            }
        ],
        "must_have_anchors": {},
        "extraction_health": "ok"
    }
    
    cleaner = Cleaner()
    res = cleaner.clean(doc)
    
    cleaned_sections = {s["name"]: s["text"] for s in res["sections"]}
    
    # 1. FAQs section must be dropped entirely
    assert "FAQs" not in cleaned_sections
    
    # 2. Boilerplate "Read all scheme related documents carefully" must be stripped
    # 3. Currency Rs. / Rs / INR must be normalized to ₹
    # 4. Word boundary check: "manager" and "years" must be untouched (no manage₹ or yea₹)
    expense_text = cleaned_sections["Expense Ratio"]
    assert "Read all scheme related documents carefully" not in expense_text
    assert "Rs" not in expense_text
    assert "INR" not in expense_text
    assert "₹0.77%" in expense_text
    assert "₹0.8%" in expense_text
    assert "₹ 0.77" in expense_text

    
    manager_text = cleaned_sections["Fund Manager"]
    assert "manager" in manager_text
    assert "managers" not in manager_text
