# Phase 4 Edge Cases: Generation & Response Composition

**Architecture reference:** [Phase 4](../architecture.md#phase-4-generation--response-composition)

---

## Context packing

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P4-01 | Top-k chunks from two schemes (ambiguous query) | Packer prefers single scheme or passes note “multiple schemes”—generator must not merge facts | High |
| P4-02 | Context exceeds LLM token limit | Drop lowest-score chunks first; keep highest + citation metadata | High |
| P4-03 | Duplicate chunks in top-k | Deduplicate by `chunk_id` before prompt | Medium |
| P4-04 | Retrieved context empty (bug bypass) | Do not call LLM; return not-found template | Critical |
| P4-05 | Context contradicts (two different exit loads same scheme) | Prefer newer `fetched_at` or single chunk; else not-found | High |

## LLM generation

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P4-06 | LLM returns 4+ sentences | Post-validator fails; retry once with stricter prompt; then truncate or template | High |
| P4-07 | LLM adds “I recommend” despite instructions | Post-validator → refusal path (Phase 5) or strip and retry | Critical |
| P4-08 | LLM cites `https://www.sebi.gov.in/...` | Citation override to chunk `source_url` from closed set | Critical |
| P4-09 | LLM cites correct domain but sixth Groww fund path | Override to retrieved chunk URL only | Critical |
| P4-10 | LLM invents expense ratio not in context | Grounding check: numbers in answer must appear in context strings | Critical |
| P4-11 | LLM outputs markdown link `[text](url)` | Normalize to plain URL line for UI; one URL only | Medium |
| P4-12 | LLM refuses despite factual context | Retry; if still refusing, template answer from top chunk | Medium |
| P4-13 | Structured JSON mode returns invalid JSON | Fallback to plain text parse or single retry | Medium |
| P4-14 | API timeout mid-generation | Return user-friendly error; no partial uncited answer | High |

## Citation & footer

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P4-15 | Two URLs in response | Validator fails; keep `source_url` of top chunk only | Critical |
| P4-16 | No URL in response | Inject citation from highest-score chunk | High |
| P4-17 | `source_last_updated` null for all chunks | Footer uses max `fetched_at` date (date part only) | Medium |
| P4-18 | Footer date in future (bad page metadata) | Clamp to `fetched_at` or today UTC; log anomaly | Medium |
| P4-19 | Footer missing after composer bug | CI test fails; never ship response without footer | Critical |
| P4-20 | Citation URL scheme is `http://` | Upgrade to `https://` canonical | Low |

## Format & compliance

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P4-21 | Answer includes performance comparison | Block; use performance template (one sentence + scheme URL) | Critical |
| P4-22 | “Which fund is better” phrased as factual | Should be caught in Phase 5 pre-gate; if reaches LLM, post-filter refusal | Critical |
| P4-23 | Answer includes phone/email support from page footer | Omit PII/support CTAs from answer text | Medium |
| P4-24 | Bullet list counts as one sentence | Per Phase 0 rule: disallow bullets or count each line | Medium |
| P4-25 | Not-found template still needs citation | Cite best-match scheme URL from closed set | High |

## Performance-query template

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P4-26 | “3 year CAGR for ELSS?” | Template: direct to ELSS Groww page; no CAGR value in text | Critical |
| P4-27 | “Show last 5 year returns vs Nifty” | Same; no Nifty comparison | Critical |
| P4-28 | Page chunk contains return numbers; user asks return | Still do not summarize—template only per architecture | High |

## Retry & fallbacks

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P4-29 | Validator fails twice | Safe fallback: not-found + citation + footer | High |
| P4-30 | Temperature &gt; 0.3 configured | Document risk; default 0–0.3 for production | Medium |

---

## Test hints (Phase 4)

- Automated: sentence count ≤ 3; exactly one URL; URL ∈ allowlist; footer regex match.
- Adversarial prompts with poisoned context containing fake ratios—answer must not include them.
- Mock LLM returning SEBI URL → assert override to Groww allowlist URL.
