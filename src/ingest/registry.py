"""Ingest registry gate — pre-flight validation before any HTTP fetch."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from src.foundation.allowlist import CLOSED_CORPUS_URLS, is_allowed_url, normalize_url
from src.foundation.loader import CONFIG_DIR, DATA_DIR, load_amc_config, load_registry
from src.foundation.models import AmcConfig, RegistryEntry
from src.foundation.validators import ValidationResult, validate_amc_config, validate_registry

# Detect URLs anywhere in CSV cell values (P1-03).
_URL_IN_TEXT = re.compile(r"https?://[^\s,\"']+", re.IGNORECASE)


@dataclass(frozen=True)
class IngestRegistry:
    """Validated registry ready for fetch."""

    config: AmcConfig
    entries: list[RegistryEntry]

    @property
    def urls(self) -> tuple[str, ...]:
        return tuple(e.url for e in self.entries)

    def url_for_slug(self, slug: str) -> str | None:
        for entry in self.entries:
            if entry.scheme_slug == slug:
                return entry.url
        return None


@dataclass
class RegistryGateResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    registry: IngestRegistry | None = None

    def fail(self, message: str) -> None:
        self.ok = False
        self.errors.append(message)


class RegistryGateError(Exception):
    """Raised when pre-flight fails; ingest must not perform HTTP."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"Registry gate failed with {len(errors)} error(s)")


def _scan_csv_cells_for_urls(registry_path: Path, result: RegistryGateResult) -> None:
    """Reject registry files that embed non-allowlisted URLs in any column."""
    if not registry_path.is_file():
        result.fail(f"Registry file not found: {registry_path}")
        return

    with registry_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            result.fail("url_registry.csv has no header row")
            return
        for row_num, row in enumerate(reader, start=2):
            for column, value in row.items():
                if not value:
                    continue
                for raw_url in _URL_IN_TEXT.findall(value):
                    cleaned = raw_url.rstrip(").]")
                    canonical = normalize_url(cleaned)
                    if not is_allowed_url(canonical):
                        result.fail(
                            f"Row {row_num}, column {column!r}: "
                            f"non-allowlisted URL {canonical!r}"
                        )


def _validate_registry_non_empty(registry: list[RegistryEntry], result: ValidationResult) -> None:
    if not registry:
        result.fail("url_registry.csv is empty; abort ingest before HTTP")


def _validate_exact_corpus_urls(registry: list[RegistryEntry], result: ValidationResult) -> None:
    registry_urls = {e.url for e in registry}
    if registry_urls != set(CLOSED_CORPUS_URLS):
        missing = CLOSED_CORPUS_URLS - registry_urls
        extra = registry_urls - CLOSED_CORPUS_URLS
        if missing:
            result.fail(f"Registry missing closed corpus URLs: {sorted(missing)}")
        if extra:
            result.fail(f"Registry contains URLs outside closed corpus: {sorted(extra)}")


def run_registry_gate(
    registry_path: Path | None = None,
    amc_path: Path | None = None,
) -> RegistryGateResult:
    """
    Run ingest pre-flight checks.
    Does not perform HTTP; safe to call before HTTP fetch.
    """
    registry_path = registry_path or DATA_DIR / "url_registry.csv"
    amc_path = amc_path or CONFIG_DIR / "amc.yaml"
    gate = RegistryGateResult()

    _scan_csv_cells_for_urls(registry_path, gate)
    if not gate.ok:
        return gate

    try:
        config = load_amc_config(amc_path)
        registry = load_registry(registry_path)
    except (OSError, ValueError, KeyError) as exc:
        gate.fail(f"Failed to load config/registry: {exc}")
        return gate

    foundation = ValidationResult()
    validate_amc_config(config, foundation)
    _validate_registry_non_empty(registry, foundation)
    validate_registry(registry, config, foundation)
    _validate_exact_corpus_urls(registry, foundation)

    for err in foundation.errors:
        gate.fail(err)

    if gate.ok:
        gate.registry = IngestRegistry(config=config, entries=registry)
    return gate


def preflight_registry(
    registry_path: Path | None = None,
    amc_path: Path | None = None,
) -> IngestRegistry:
    """Return validated ingest registry or raise RegistryGateError."""
    gate = run_registry_gate(registry_path=registry_path, amc_path=amc_path)
    if gate.ok and gate.registry is not None:
        return gate.registry
    raise RegistryGateError(gate.errors)


def run_cli() -> int:
    """CLI entry point for preflight check."""
    gate = run_registry_gate()
    if gate.ok and gate.registry is not None:
        print(f"Pre-flight registry gate passed ({len(gate.registry.entries)} URLs).")
        print("Ready for ingestion fetch.")
        return 0
    print("Pre-flight registry gate failed:")
    for err in gate.errors:
        print(f"  - {err}")
    return 1
