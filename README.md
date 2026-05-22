# Groww Mutual Fund RAG Assistant

Facts-only FAQ assistant for **HDFC Mutual Fund** schemes using a **closed corpus** of five [Groww](https://groww.in) scheme pages. No investment advice; every answer cites exactly one source URL from that set.

**Disclaimer:** Facts-only. No investment advice.

## Selected AMC and schemes

| AMC | HDFC Mutual Fund |
|-----|------------------|
| Corpus | Exactly **5** Groww URLs (no other sources) |

| Scheme | Category | URL |
|--------|----------|-----|
| HDFC Mid Cap Fund Direct Growth | Mid-cap | https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth |
| HDFC Equity Fund Direct Growth | Diversified equity | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| HDFC Focused Fund Direct Growth | Focused equity | https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth |
| HDFC ELSS Tax Saver Fund Direct Plan Growth | ELSS | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |
| HDFC Large Cap Fund Direct Growth | Large-cap | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |

## Architecture

RAG pipeline over the closed corpus: ingest → chunk → embed → retrieve → generate with guardrails. See [docs/architecture.md](docs/architecture.md) and [docs/complianceRules.md](docs/complianceRules.md).

## Project structure

```
├── config/           # amc.yaml, aliases, refusal links, prompts (later phases)
├── data/
│   ├── url_registry.csv
│   ├── raw/          # Phase 1: fetched HTML
│   └── processed/    # Phase 2: chunks
├── src/
│   ├── foundation/   # Phase 0: config + validation ✓
│   ├── ingest/       # Phase 1 (subphases/phase_1_1_registry … phase_1_7_refresh)
│   ├── index/        # Phase 3
│   ├── retrieval/    # Phase 3
│   ├── generation/   # Phase 4
│   ├── guardrails/   # Phase 5
│   └── api/          # Phase 6
├── ui/               # Phase 6
├── eval/             # golden_queries.jsonl
├── tests/
└── docs/
```

## Setup (Phase 0)

Requires **Python 3.11+**.

```bash
cd "Groww Mutual Fund RAG Assistant"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Validate Phase 0 exit criteria:

```bash
python -m src.foundation.validate
pytest
```

Phase 1.1 registry gate (pre-flight, no HTTP):

```bash
python -m src.ingest preflight
# or
python -m src.ingest 1.1
```

## Implementation status

| Phase | Status |
|-------|--------|
| 0 — Foundation & compliance | Done |
| 1.1 — Registry gate | Done |
| 1.2–1.7 — Corpus acquisition | Pending |
| 2 — Processing & chunking | Pending |
| 3 — Indexing & retrieval | Pending |
| 4 — Generation | Pending |
| 5 — Guardrails | Pending |
| 6 — UI & API | Pending |
| 7 — Testing & eval | Pending |
| 8 — Deploy & docs | Pending |

## Known limitations

- Only the five Groww scheme pages above are used; facts not on those pages cannot be answered from other sources.
- Answers are limited to three sentences with one citation and a last-updated footer.
- No personalized or account-level support; PII is blocked.

## Edge cases

Per-phase edge case specs: [docs/edge-cases/README.md](docs/edge-cases/README.md).
