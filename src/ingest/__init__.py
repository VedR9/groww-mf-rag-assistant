"""Phase 1: corpus fetch and provenance (by subphase under subphases/)."""

from src.ingest.registry import (
    IngestRegistry,
    RegistryGateError,
    RegistryGateResult,
    preflight_registry,
    run_registry_gate,
)

__all__ = [
    "IngestRegistry",
    "RegistryGateError",
    "RegistryGateResult",
    "preflight_registry",
    "run_registry_gate",
]
