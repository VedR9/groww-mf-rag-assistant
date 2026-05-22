# Phase 7 Edge Cases: Testing, Evaluation & Quality Assurance

**Architecture reference:** [Phase 7](../architecture.md#phase-7-testing-evaluation--quality-assurance)

---

## Golden eval set design

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P7-01 | Golden answer references fact removed after page update | Eval fails; update golden or re-ingest—document drift process | High |
| P7-02 | Golden expects wrong scheme URL | Fix golden; citation must match scheme | Critical |
| P7-03 | Golden has no `expected_citation_url` | Required field for automated citation tests | High |
| P7-04 | All golden queries hit same scheme | Balance across five schemes | Medium |
| P7-05 | Golden includes comparative return question | Should be in **refusal** set, not factual set | Critical |
| P7-06 | `not_found: true` cases missing from golden | Add queries for absent corpus facts | High |

## Retrieval metrics

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P7-07 | Hit@3 passes but generation wrong | Track gen accuracy separately; do not ship on retrieval alone | High |
| P7-08 | Threshold tuned to 100% Hit@3 on train only | Hold-out query set; avoid overfit | Medium |
| P7-09 | MRR skewed by duplicate chunks | Deduplicate chunk IDs in metric script | Low |
| P7-10 | Eval run without rebuilt index after re-chunk | CI fails if index hash ≠ chunks hash | High |

## Generation & citation tests

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P7-11 | Test accepts any `groww.in` URL | Assert exact path ∈ five URL allowlist | Critical |
| P7-12 | Sentence count test ignores footer | Footer excluded from sentence count | Medium |
| P7-13 | Footer regex too strict (locale dates) | Support `YYYY-MM-DD` only per spec | Medium |
| P7-14 | LLM nondeterminism flakes CI | Fixed seed, low temperature, or snapshot tolerance rules | Medium |
| P7-15 | Mock LLM in CI; prod uses real API | Separate integration nightly job | Low |

## Refusal & compliance eval

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P7-16 | Advisory set too small (n=2) | Minimum ~15–20 advisory variants | High |
| P7-17 | Refusal test allows HTTP 200 on non-allowlist edu link | Strict URL equality check | Critical |
| P7-18 | PII test logs blocked query to file | Assert no write of raw PII | Critical |
| P7-19 | Advice phrase list incomplete (“allocate”, “portfolio”) | Extend banned phrase list iteratively | Medium |
| P7-20 | False refusal rate not measured | Track factual set refusals; alert if &gt; 5% | High |

## Integration & regression

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P7-21 | Corpus refresh changes hash; citations break | Regression job compares citation URLs still valid | High |
| P7-22 | Partial ingest (4/5 pages) in CI | CI uses full fixture corpus or mocks | Medium |
| P7-23 | E2E depends on live Groww | Use recorded HTML fixtures; live smoke weekly only | High |
| P7-24 | Unit tests pass; API contract drift | Contract test on `/api/chat` JSON schema | Medium |
| P7-25 | Performance test in CI exceeds 5s | Mark slow job optional; track p95 trend | Low |

## Reporting & gates

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P7-26 | Release with Hit@3 85% (&lt; 90% target) | Document waiver or block release per exit criteria | High |
| P7-27 | Manual spot-check skipped | Checklist item required for factual accuracy | High |
| P7-28 | Eval reports log full user queries with PII | Reports use `query_hash` only | Critical |
| P7-29 | Flaky test ignored with `@skip` | No skip on citation/compliance tests without ticket | High |
| P7-30 | Two eval harnesses (duplicate) | Single source `eval/golden_queries.jsonl` | Medium |

---

## Test hints (Phase 7)

- CI pipeline: unit → integration (fixtures) → RAG eval → refusal eval → optional live smoke.
- Release gate: 100% advisory refusal; 100% citations ∈ allowlist; Hit@3 ≥ 90% on in-corpus golden set.
