# Phase 2 Edge Cases: Document Processing & Chunking

**Architecture reference:** [Phase 2](../architecture.md#phase-2-document-processing--chunking)  
**Input:** Raw HTML from five Groww scheme pages.

---

## HTML parsing

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P2-01 | Page is mostly client-rendered (empty shell in raw HTML) | Detect low text yield; flag scheme; chunks may be empty—downstream not-found | Critical |
| P2-02 | Malformed HTML / unclosed tags | Parser recovers; no crash; log warning | High |
| P2-03 | Duplicate nav/header/footer in extracted text | Strip boilerplate; dedupe repeated menus | Medium |
| P2-04 | Hindi/regional labels mixed with English | Keep Unicode; normalize whitespace; `scheme_name` still English canonical | Medium |
| P2-05 | Numeric values with `₹`, `,`, `%` | Preserve in chunk text; do not parse as advice | Low |
| P2-06 | “Expense ratio” label missing but value in table | Table flattening attaches nearest header | High |
| P2-07 | Multiple tables with similar headers | Section context in `section_title` metadata | Medium |

## Chunking

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P2-08 | Single section exceeds max token size (1024+) | Split with overlap; same `source_url` and `scheme_name` | High |
| P2-09 | Very short page yields zero chunks | Fail Phase 2 exit for that scheme; block index build | Critical |
| P2-10 | Overlap causes near-duplicate chunks | Acceptable for retrieval; dedupe at context-pack time (Phase 4) | Low |
| P2-11 | Performance chart data as long JSON in DOM | Index labels only; omit raw time series if per architecture | High |
| P2-12 | ELSS lock-in on ELSS page vs absent on large-cap page | ELSS chunks contain lock-in; other schemes omit—not hallucinate | High |
| P2-13 | “How to download statement” not on any page | No chunk; eval expects not-found at answer time | High |
| P2-14 | FAQ accordion collapsed in HTML | Extract hidden accordion text if present in DOM; else not in corpus | Medium |

## Metadata enrichment

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P2-15 | `source_url` missing on chunk | Reject chunk at write time | Critical |
| P2-16 | `source_url` set to relative path `/mutual-funds/...` | Resolve to full allowlisted HTTPS URL | High |
| P2-17 | On-page “last updated” not found | `source_last_updated: null`; Phase 4 uses `fetched_at` | Medium |
| P2-18 | Conflicting dates in footer vs meta | Prefer explicit on-page date; log conflict | Medium |
| P2-19 | Wrong `scheme_name` attached (cross-page bleed) | One raw file per scheme; never merge HTML across slugs | Critical |
| P2-20 | `document_type` not `scheme_page` | Normalizer forces enum; reject invalid | Medium |

## Content compliance (chunk text)

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P2-21 | Page contains “best fund”, “recommend” in marketing copy | Store verbatim in chunks; Phase 5 must not generate advice from it | High |
| P2-22 | Comparative returns vs category on page | Chunk may contain numbers; Phase 4 must not summarize/compare in answers | High |
| P2-23 | External link text “Download KIM from HDFC” | Do not fetch; chunk may mention label without URL to non-allowlisted domain | Medium |

## Storage & idempotency

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P2-24 | Re-run Phase 2 without deleting old chunks | Replace by `content_hash` or full rebuild of `chunks.jsonl` | Medium |
| P2-25 | `chunk_id` changes on re-run | Re-embed all in Phase 3; document rebuild procedure | Medium |
| P2-26 | Corrupt `chunks.jsonl` mid-write | Atomic write (temp file + rename) | High |

---

## Test hints (Phase 2)

- Fixture HTML per scheme: assert `source_url` ∈ allowlist for every chunk.
- Assert expense ratio / exit load fields produce ≥1 chunk when present in fixture.
- Empty parse fixture → zero chunks → pipeline flags scheme.
