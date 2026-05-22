# Compliance Rules: Facts-Only Mutual Fund FAQ Assistant

This document defines response, citation, and refusal policies for the HDFC Groww closed-corpus RAG assistant. All implementation phases must conform to these rules.

**Corpus:** Exactly five Groww scheme URLs listed in `config/amc.yaml` and `data/url_registry.csv`. No AMC, AMFI, SEBI, or other Groww pages may be fetched, indexed, or cited.

---

## 1. Facts-only scope

### Allowed (factual)

- Expense ratio, exit load, minimum SIP, lock-in period, riskometer, benchmark index
- Fund category, plan type (Direct Growth), AMC name
- Factual descriptions present on the indexed scheme page

### Not allowed (advisory or subjective)

- Investment recommendations (“should I invest”, “is it good”)
- Fund comparisons (“which is better”, “higher return than”)
- Return predictions or performance opinions
- Asset allocation or portfolio advice

### Performance-related queries

- Do **not** state, calculate, or compare returns, CAGR, or NAV performance
- Use the performance template: one sentence directing the user to the scheme’s Groww page for performance data, plus that page’s URL from the closed set and the standard footer

---

## 2. Response format

| Rule | Specification |
|------|----------------|
| Max length | **3 sentences** maximum in the answer body |
| Sentence counting | Split on `.`, `!`, `?` after trimming; empty segments ignored |
| Excluded from count | Footer line; standalone citation URL line |
| Bullets | Avoid bullet lists; if used, each bullet line counts as a sentence |
| Citations | **Exactly one** URL per response |
| Citation allowlist | Must be an exact match to one of the five closed corpus URLs |
| Footer | Required on every response (including refusals and not-found): `Last updated from sources: YYYY-MM-DD` |
| Footer date | Use `source_last_updated` from retrieved chunks when available; else max `fetched_at` date (UTC, date part only) |

---

## 3. Not found

When a fact is not present on the relevant scheme page(s), or retrieval score is below threshold:

- State clearly that the information could not be verified on the scheme pages in use
- Do not invent facts or add new URLs
- Cite the **best-matching** scheme URL from the closed five (same scheme if known, else default from `config/amc.yaml`)

---

## 4. Refusal handling

### When to refuse (pre-generation)

- Advisory or subjective intent
- Fund comparison or recommendation requests
- Predictions (“will it beat Nifty”)
- Jailbreaks instructing the model to ignore rules

### Refusal response

1. Polite, fixed-tone message reinforcing facts-only limitation
2. Optional one-line redirect (no advice)
3. **Exactly one** citation URL from the closed five (`config/refusal_links.yaml`)
4. Standard footer

### PII and account data

- Do not collect, store, or process: PAN, Aadhaar, account numbers, OTPs, email, phone
- Hard-block queries containing PII patterns; do not log raw PII

---

## 5. Privacy and logging

Audit logs may contain: `timestamp`, `query_hash`, `intent_label`, `refused`, `citation_url`, `latency_ms`.

Audit logs must **not** contain raw user queries when PII is detected, or full PAN/account payloads.

---

## 6. Disclaimer (UI and README)

Display persistently in the UI:

**Facts-only. No investment advice.**

---

## 7. Phase 0 validation

Before Phase 1 ingest, run:

```bash
python -m src.foundation.validate
```

This enforces: five URL registry rows, YAML/CSV alignment, alias uniqueness, and golden eval citation allowlist.
