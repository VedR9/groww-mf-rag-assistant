"""Data models for Phase 0 configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scheme:
    name: str
    slug: str
    category: str
    url: str


@dataclass(frozen=True)
class AmcConfig:
    amc: str
    reference_context: str
    corpus_policy: str
    corpus_size: int
    schemes: list[Scheme]
    default_scheme_slug: str

    @property
    def slug_to_url(self) -> dict[str, str]:
        return {s.slug: s.url for s in self.schemes}

    @property
    def url_to_slug(self) -> dict[str, str]:
        return {s.url: s.slug for s in self.schemes}


@dataclass(frozen=True)
class RegistryEntry:
    scheme_slug: str
    scheme_name: str
    category: str
    url: str
    priority: str
    refresh_cadence: str
