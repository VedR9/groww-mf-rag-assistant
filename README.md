---
title: Groww MF Rag Backend
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---
# Groww Mutual Fund RAG Assistant

Facts-only FAQ assistant for **HDFC Mutual Fund** schemes using a **closed corpus** of five [Groww](https://groww.in) scheme pages. No investment advice; every answer cites exactly one source URL from that set.

**Disclaimer:** Facts-only. No investment advice.

## 🚀 Live Deployment
- **Frontend (Vercel):** [Groww MF RAG Assistant UI](https://groww-mf-rag-assistant.vercel.app/)--> Hosted on a free server, first time launch can time tike upto 50 seconds.
- **Backend API (HuggingFace Spaces):** Hosted via Docker container with 16GB RAM
- **Automation (GitHub Actions):** Scrapes the Groww URLs daily at 10:00 AM IST, rebuilds the FAISS vector index, and automatically pushes the fresh data to HuggingFace.

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


https://github.com/user-attachments/assets/ed22027a-5bde-4538-ad95-fa69afa9df31

## Architecture

RAG pipeline over the closed corpus: ingest → chunk → embed → retrieve → generate with guardrails. See [docs/architecture.md](docs/architecture.md) and [docs/complianceRules.md](docs/complianceRules.md).

- **Frontend:** React + Vite + TailwindCSS
- **Backend:** FastAPI, Python 3.11
- **Vector Database:** FAISS
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2`
- **LLM:** Groq API (`llama3-8b-8192`)

## Project structure

```
├── config/           # amc.yaml, aliases, refusal links, prompts
├── data/
│   ├── url_registry.csv
│   ├── raw/          # Phase 1: fetched HTML
│   └── processed/    # Phase 2: chunks
├── src/
│   ├── foundation/   # Phase 0: config + validation
│   ├── ingest/       # Phase 1: ingestion pipeline
│   ├── index/        # Phase 3: indexing
│   ├── retrieval/    # Phase 3: retrieval
│   ├── generation/   # Phase 4: generation
│   ├── guardrails/   # Phase 5: guardrails
│   └── api/          # Phase 6: fastAPI backend
├── ui/               # Phase 6: React frontend
├── eval/             # golden_queries.jsonl
├── tests/
└── docs/
```

## Setup & Local Development

Requires **Python 3.11+**.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

To run the full data scraping and indexing pipeline locally:
```bash
python -m src.ingest 1.7
```

To run the FastAPI backend:
```bash
uvicorn src.api.main:app --reload
```

## Implementation status

| Phase | Status |
|-------|--------|
| 0 — Foundation & compliance | ✅ Done |
| 1.1 — Registry gate | ✅ Done |
| 1.2–1.7 — Corpus acquisition | ✅ Done |
| 2 — Processing & chunking | ✅ Done |
| 3 — Indexing & retrieval | ✅ Done |
| 4 — Generation | ✅ Done |
| 5 — Guardrails | ✅ Done |
| 6 — UI & API | ✅ Done |
| 7 — Testing & eval | ✅ Done |
| 8 — Deploy & docs | ✅ Done |

## Known limitations

- Only the five Groww scheme pages above are used; facts not on those pages cannot be answered from other sources.
- Answers are limited to three sentences with one citation and a last-updated footer.
- No personalized or account-level support; PII is blocked.

## Edge cases

Per-phase edge case specs: [docs/edge-cases/README.md](docs/edge-cases/README.md).
