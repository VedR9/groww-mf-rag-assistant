# Phase 3 Edge Cases: Indexing & Retrieval

**Architecture reference:** [Phase 3](../architecture.md#phase-3-indexing--retrieval)

---

## Embedding & index build

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P3-01 | Embedding API key missing | Fail index build with clear error; no silent zero vectors | Critical |
| P3-02 | Embedding API rate limit mid-batch | Resume from last `chunk_id`; idempotent batch | High |
| P3-03 | One chunk text empty string | Skip embed; log warning | High |
| P3-04 | Vector dimension mismatch on re-embed | Rebuild entire index; version metadata on collection | Critical |
| P3-05 | Only 4 schemes indexed (one failed Phase 2) | Retriever works partial; queries for missing scheme → not found | High |
| P3-06 | Duplicate `chunk_id` in index | Last write wins or dedupe on ingest to index | Medium |

## Query handling & filters

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P3-07 | Query names “HDFC Mid Cap” explicitly | Metadata filter `scheme_name` → mid-cap URL chunks only | High |
| P3-08 | Query names wrong AMC (“SBI Bluechip”) | No filter match; low scores → not found; no SBI URL | Critical |
| P3-09 | Query mentions two schemes (“mid cap vs large cap expense”) | No comparison; retrieve separately or ask to split—policy in Phase 4/5 | High |
| P3-10 | Typo: “expence ratio” | Hybrid/BM25 or embedding still retrieves “expense ratio” chunk if present | Medium |
| P3-11 | Query in Hindi | Low retrieval quality; not-found or English-only message | Medium |
| P3-12 | Empty query string | API/UI validation error; no retrieval | High |
| P3-13 | Very long query (paste of article) | Truncate query embedding input; guardrails may refuse | Medium |

## Scores & thresholds

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P3-14 | Top score below threshold (0.65 hypothetical) | Not-found path; do not pass weak context to LLM | Critical |
| P3-15 | Top score high but wrong scheme (embedding confusion) | Scheme filter when entity detected; else rerank by scheme metadata | High |
| P3-16 | All top-k from same nav boilerplate chunk | Rerank/downrank boilerplate; tune chunking in Phase 2 | Medium |
| P3-17 | Tie scores for two schemes | Prefer chunk with matching `scheme_name` entity; else clarify | Medium |
| P3-18 | `top_k=5` but only 2 chunks exist for scheme | Return 2; no padding with other schemes unless unfiltered query | Low |

## Special query types (retrieval policy)

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P3-19 | “What is the 1Y return?” | Retrieve scheme page chunk if exists; Phase 4 must not compute—cite URL only | Critical |
| P3-20 | “Compare ELSS and large cap returns” | Retrieval optional; Phase 5 should refuse advisory/comparison | Critical |
| P3-21 | “How to download capital gains report” | Retrieve only if phrase in corpus; else not-found | High |
| P3-22 | “Benchmark index for focused fund” | Filter focused fund; retrieve benchmark chunk or not-found | High |
| P3-23 | “Minimum SIP” generic (no scheme) | Search all five; if multiple values, Phase 4 lists conflict or asks clarify | High |
| P3-24 | “Riskometer” for scheme without label on page | Not-found with citation to that scheme’s URL | Medium |

## Hybrid search (optional)

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P3-25 | Vector finds wrong chunk; BM25 finds “exit load” exact | Fusion boosts correct regulatory field chunk | Medium |
| P3-26 | BM25 disabled | Pure vector; document metric impact in eval | Low |

## Performance & ops

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P3-27 | Index file missing on API start | Health check fails; `/chat` returns 503 | High |
| P3-28 | Query latency &gt; 5s p95 | Log slow retrieval; reduce top_k or cache embeddings | Medium |
| P3-29 | Memory pressure loading full index | Use on-disk FAISS/Chroma; document min RAM | Medium |

---

## Test hints (Phase 3)

- Golden queries: Hit@3 ≥ 90% on in-corpus facts only.
- Adversarial: “SBI fund” → no citation outside allowlist.
- Threshold sweep: document score cutoffs where hallucination rate increases.
