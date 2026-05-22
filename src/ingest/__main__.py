"""Ingest CLI — dispatch to Phase 1 subphases."""

from __future__ import annotations

import argparse
import sys

from src.ingest.registry import RegistryGateError, run_cli as run_preflight
from src.ingest.subphases.phase_1_1_fetcher.cli import run as run_fetcher
from src.ingest.subphases.phase_1_2_extractor.cli import run as run_extractor
from src.ingest.subphases.phase_1_3_cleaner.cli import run as run_cleaner
from src.ingest.subphases.phase_1_4_chunker.cli import run as run_chunker
from src.ingest.subphases.phase_1_5_embedder.cli import run as run_embedder
from src.ingest.subphases.phase_1_6_indexer.cli import run as run_indexer
from src.ingest.subphases.phase_1_7_refresh.cli import run as run_refresh

_SUBPHASE_COMMANDS = {
    "preflight": ("preflight", run_preflight),
    "1.1": ("1.1", run_fetcher),
    "fetch": ("1.1", run_fetcher),
    "1.2": ("1.2", run_extractor),
    "extract": ("1.2", run_extractor),
    "1.3": ("1.3", run_cleaner),
    "clean": ("1.3", run_cleaner),
    "1.4": ("1.4", run_chunker),
    "chunk": ("1.4", run_chunker),
    "1.5": ("1.5", run_embedder),
    "embed": ("1.5", run_embedder),
    "1.6": ("1.6", run_indexer),
    "index": ("1.6", run_indexer),
    "1.7": ("1.7", run_refresh),
    "refresh": ("1.7", run_refresh),
}



def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Groww MF corpus ingest (Phase 1 subphases)."
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="preflight",
        help="preflight = registry gate; 1.1/fetch = robust crawl fetcher; more commands added in 1.2–1.7",
    )
    args, remaining = parser.parse_known_args(argv)

    handler = _SUBPHASE_COMMANDS.get(args.command)
    if handler is None:
        known = ", ".join(sorted(_SUBPHASE_COMMANDS))
        print(f"Unknown command {args.command!r}. Available: {known}")
        return 1

    _label, run_fn = handler
    return run_fn()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RegistryGateError as exc:
        print("Pre-flight registry gate failed:")
        for err in exc.errors:
            print(f"  - {err}")
        raise SystemExit(1) from exc
