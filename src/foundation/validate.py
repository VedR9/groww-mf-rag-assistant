"""CLI entrypoint: python -m src.foundation.validate"""

from __future__ import annotations

import sys

from src.foundation.validators import validate_phase0


def main() -> int:
    result = validate_phase0()
    if result.ok:
        print("Phase 0 validation passed.")
        return 0
    print("Phase 0 validation failed:")
    for err in result.errors:
        print(f"  - {err}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
