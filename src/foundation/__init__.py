"""Phase 0: configuration, closed corpus allowlist, and validation."""

from src.foundation.allowlist import CLOSED_CORPUS_URLS, CORPUS_SIZE, is_allowed_url, normalize_url
from src.foundation.models import AmcConfig, RegistryEntry, Scheme
from src.foundation.loader import load_amc_config, load_registry, load_scheme_aliases, load_refusal_links

__all__ = [
    "CLOSED_CORPUS_URLS",
    "CORPUS_SIZE",
    "is_allowed_url",
    "normalize_url",
    "AmcConfig",
    "RegistryEntry",
    "Scheme",
    "load_amc_config",
    "load_registry",
    "load_scheme_aliases",
    "load_refusal_links",
]
