"""Phase 0 validation and allowlist tests."""

from __future__ import annotations

import pytest

from src.foundation.allowlist import CLOSED_CORPUS_URLS, CORPUS_SIZE, is_allowed_url, normalize_url
from src.foundation.loader import load_amc_config, load_golden_queries, load_registry
from src.foundation.validators import validate_phase0


def test_corpus_size_is_five():
    assert CORPUS_SIZE == 5
    assert len(CLOSED_CORPUS_URLS) == 5


def test_normalize_strips_trailing_slash_and_query():
    url = "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth/?utm=1"
    assert normalize_url(url) == "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth"


def test_rejects_non_allowlist_groww_path():
    assert not is_allowed_url("https://groww.in/blog/some-post")


def test_registry_row_count():
    assert len(load_registry()) == 5


def test_amc_yaml_matches_allowlist():
    config = load_amc_config()
    assert {s.url for s in config.schemes} == set(CLOSED_CORPUS_URLS)


def test_golden_citations_in_allowlist():
    for row in load_golden_queries():
        citation = row.get("expected_citation_url")
        if row.get("expected_behavior") == "block":
            assert citation is None
        else:
            assert citation in CLOSED_CORPUS_URLS


def test_phase0_validation_passes():
    result = validate_phase0()
    assert result.ok, result.errors
