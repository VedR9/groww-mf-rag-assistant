"""Closed corpus URL allowlist — single source of truth for permitted URLs."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse

# Frozen set of five Groww HDFC scheme pages (Phase 0).
CLOSED_CORPUS_URLS: frozenset[str] = frozenset(
    {
        "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
    }
)

CORPUS_SIZE = len(CLOSED_CORPUS_URLS)

ALLOWED_NETLOC = "groww.in"


def normalize_url(url: str) -> str:
    """Canonical HTTPS form without trailing slash or query params."""
    parsed = urlparse(url.strip())
    if not parsed.scheme:
        parsed = urlparse(f"https://{url.strip()}")
    scheme = "https"
    netloc = (parsed.netloc or "").lower()
    path = parsed.path.rstrip("/")
    return urlunparse((scheme, netloc, path, "", "", ""))


def is_allowed_url(url: str) -> bool:
    return normalize_url(url) in CLOSED_CORPUS_URLS


def url_for_slug(slug: str, slug_to_url: dict[str, str]) -> str | None:
    return slug_to_url.get(slug)
