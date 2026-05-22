"""Load Phase 0 configuration files from the project root."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

from src.foundation.allowlist import normalize_url
from src.foundation.models import AmcConfig, RegistryEntry, Scheme

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
EVAL_DIR = PROJECT_ROOT / "eval"


def _read_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_amc_config(path: Path | None = None) -> AmcConfig:
    path = path or CONFIG_DIR / "amc.yaml"
    raw = _read_yaml(path)
    schemes = [
        Scheme(
            name=s["name"],
            slug=s["slug"],
            category=s["category"],
            url=normalize_url(s["url"]),
        )
        for s in raw["schemes"]
    ]
    return AmcConfig(
        amc=raw["amc"],
        reference_context=raw["reference_context"],
        corpus_policy=raw["corpus_policy"],
        corpus_size=int(raw["corpus_size"]),
        schemes=schemes,
        default_scheme_slug=raw["default_scheme_slug"],
    )


def load_registry(path: Path | None = None) -> list[RegistryEntry]:
    path = path or DATA_DIR / "url_registry.csv"
    entries: list[RegistryEntry] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(
                RegistryEntry(
                    scheme_slug=row["scheme_slug"].strip(),
                    scheme_name=row["scheme_name"].strip(),
                    category=row["category"].strip(),
                    url=normalize_url(row["url"]),
                    priority=row["priority"].strip(),
                    refresh_cadence=row["refresh_cadence"].strip(),
                )
            )
    return entries


def load_scheme_aliases(path: Path | None = None) -> dict[str, list[str]]:
    path = path or CONFIG_DIR / "scheme_aliases.yaml"
    raw = _read_yaml(path)
    return {slug: [a.lower() for a in aliases] for slug, aliases in raw["aliases"].items()}


def load_refusal_links(path: Path | None = None) -> dict:
    path = path or CONFIG_DIR / "refusal_links.yaml"
    return _read_yaml(path)


def load_golden_queries(path: Path | None = None) -> list[dict]:
    path = path or EVAL_DIR / "golden_queries.jsonl"
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows
