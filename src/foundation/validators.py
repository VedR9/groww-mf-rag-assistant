"""Phase 0 exit-criteria validation."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.foundation.allowlist import CLOSED_CORPUS_URLS, CORPUS_SIZE, is_allowed_url, normalize_url
from src.foundation.loader import (
    load_amc_config,
    load_golden_queries,
    load_refusal_links,
    load_registry,
    load_scheme_aliases,
)
from src.foundation.models import AmcConfig, RegistryEntry

VALID_INTENTS = frozenset({"factual", "advisory", "pii"})
VALID_BEHAVIORS = frozenset(
    {"answer", "not_found", "refusal", "block", "performance_template"}
)


@dataclass
class ValidationResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.ok = False
        self.errors.append(message)


def validate_amc_config(config: AmcConfig, result: ValidationResult) -> None:
    if config.corpus_policy != "closed":
        result.fail(f"amc.yaml corpus_policy must be 'closed', got {config.corpus_policy!r}")
    if config.corpus_size != CORPUS_SIZE:
        result.fail(f"amc.yaml corpus_size must be {CORPUS_SIZE}, got {config.corpus_size}")
    if len(config.schemes) != CORPUS_SIZE:
        result.fail(f"amc.yaml must define {CORPUS_SIZE} schemes, got {len(config.schemes)}")

    slugs = [s.slug for s in config.schemes]
    if len(slugs) != len(set(slugs)):
        result.fail("Duplicate scheme slugs in amc.yaml")

    urls = [s.url for s in config.schemes]
    if len(urls) != len(set(urls)):
        result.fail("Duplicate scheme URLs in amc.yaml")

    if config.slug_to_url.get(config.default_scheme_slug) is None:
        result.fail(
            f"default_scheme_slug {config.default_scheme_slug!r} not found in schemes"
        )

    for scheme in config.schemes:
        if not is_allowed_url(scheme.url):
            result.fail(f"Scheme URL not in closed allowlist: {scheme.url}")

    allowlist_match = {s.url for s in config.schemes}
    if allowlist_match != set(CLOSED_CORPUS_URLS):
        missing = CLOSED_CORPUS_URLS - allowlist_match
        extra = allowlist_match - CLOSED_CORPUS_URLS
        if missing:
            result.fail(f"amc.yaml missing allowlist URLs: {sorted(missing)}")
        if extra:
            result.fail(f"amc.yaml has non-allowlist URLs: {sorted(extra)}")


def validate_registry(registry: list[RegistryEntry], config: AmcConfig, result: ValidationResult) -> None:
    if len(registry) != CORPUS_SIZE:
        result.fail(f"url_registry.csv must have {CORPUS_SIZE} rows, got {len(registry)}")

    registry_urls = [e.url for e in registry]
    if len(registry_urls) != len(set(registry_urls)):
        result.fail("Duplicate URLs in url_registry.csv")

    registry_slugs = [e.scheme_slug for e in registry]
    if len(registry_slugs) != len(set(registry_slugs)):
        result.fail("Duplicate scheme_slug values in url_registry.csv")

    for entry in registry:
        if not is_allowed_url(entry.url):
            result.fail(f"Registry URL not in allowlist: {entry.url}")

    config_by_slug = {s.slug: s for s in config.schemes}
    for entry in registry:
        scheme = config_by_slug.get(entry.scheme_slug)
        if scheme is None:
            result.fail(f"Registry slug {entry.scheme_slug!r} not in amc.yaml")
            continue
        if normalize_url(scheme.url) != entry.url:
            result.fail(
                f"URL mismatch for {entry.scheme_slug}: "
                f"amc.yaml={scheme.url!r} registry={entry.url!r}"
            )
        if scheme.name != entry.scheme_name:
            result.fail(f"scheme_name mismatch for {entry.scheme_slug}")
        if scheme.category != entry.category:
            result.fail(f"category mismatch for {entry.scheme_slug}")


def validate_aliases(aliases: dict[str, list[str]], config: AmcConfig, result: ValidationResult) -> None:
    valid_slugs = set(config.slug_to_url)
    for slug in aliases:
        if slug not in valid_slugs:
            result.fail(f"Alias group for unknown slug: {slug}")

    seen: dict[str, str] = {}
    for slug, terms in aliases.items():
        for term in terms:
            if term in seen:
                result.fail(
                    f"Alias {term!r} maps to both {seen[term]!r} and {slug!r}"
                )
            seen[term] = slug


def validate_refusal_links(refusal: dict, config: AmcConfig, result: ValidationResult) -> None:
    slug_to_url = config.slug_to_url
    default_slug = refusal.get("default_slug")
    if default_slug not in slug_to_url:
        result.fail(f"refusal_links default_slug invalid: {default_slug!r}")

    for intent, slug in (refusal.get("intent_map") or {}).items():
        if slug not in slug_to_url:
            result.fail(f"refusal_links intent_map[{intent!r}] has invalid slug {slug!r}")
        url = slug_to_url[slug]
        if not is_allowed_url(url):
            result.fail(f"refusal link URL not allowed: {url}")


def validate_golden_queries(queries: list[dict], config: AmcConfig, result: ValidationResult) -> None:
    if not queries:
        result.fail("golden_queries.jsonl is empty")
        return

    ids: set[str] = set()
    has_refusal = False
    has_factual = False

    for row in queries:
        qid = row.get("id")
        if not qid:
            result.fail("Golden query missing id")
            continue
        if qid in ids:
            result.fail(f"Duplicate golden query id: {qid}")
        ids.add(qid)

        intent = row.get("intent")
        if intent not in VALID_INTENTS:
            result.fail(f"{qid}: invalid intent {intent!r}")

        behavior = row.get("expected_behavior")
        if behavior not in VALID_BEHAVIORS:
            result.fail(f"{qid}: invalid expected_behavior {behavior!r}")

        if intent == "advisory":
            has_refusal = True
        if intent == "factual":
            has_factual = True

        slug = row.get("scheme_slug")
        if slug is not None and slug not in config.slug_to_url:
            result.fail(f"{qid}: unknown scheme_slug {slug!r}")

        citation = row.get("expected_citation_url")
        if behavior == "block":
            if citation is not None:
                result.fail(f"{qid}: block behavior must have null expected_citation_url")
        else:
            if not citation or not is_allowed_url(citation):
                result.fail(f"{qid}: expected_citation_url must be in closed allowlist")

    if not has_refusal:
        result.fail("golden_queries.jsonl must include advisory/refusal cases")
    if not has_factual:
        result.fail("golden_queries.jsonl must include factual cases")


def validate_phase0() -> ValidationResult:
    result = ValidationResult()
    config = load_amc_config()
    registry = load_registry()
    aliases = load_scheme_aliases()
    refusal = load_refusal_links()
    golden = load_golden_queries()

    validate_amc_config(config, result)
    validate_registry(registry, config, result)
    validate_aliases(aliases, config, result)
    validate_refusal_links(refusal, config, result)
    validate_golden_queries(golden, config, result)
    return result
