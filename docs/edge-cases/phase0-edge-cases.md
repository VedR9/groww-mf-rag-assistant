# Phase 0 Edge Cases: Foundation & Compliance Design

**Architecture reference:** [Phase 0](../architecture.md#phase-0-foundation--compliance-design)  
**Closed corpus:** Exactly five Groww HDFC scheme URLs—no additions.

---

## Configuration & URL registry

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P0-01 | `url_registry.csv` contains 6 rows (sixth URL is AMC factsheet) | Build/CI fails; loader rejects registry; document lists only five allowed URLs | Critical |
| P0-02 | `url_registry.csv` has 4 rows (one scheme missing) | Build/CI fails; exit criteria not met until all five present | Critical |
| P0-03 | Same URL listed twice for different schemes | Validation error; dedupe or fail with clear message | High |
| P0-04 | URL differs by trailing slash or `http` vs `https` | Normalize to canonical HTTPS form in config; single canonical string per scheme | High |
| P0-05 | URL path typo (e.g. `hdfc-midcap` vs `hdfc-mid-cap`) | Caught by allowlist hash match; reject at load | Critical |
| P0-06 | Developer adds sixth URL to `config/amc.yaml` only (not CSV) | Config validator cross-checks YAML ↔ CSV; fail on mismatch | High |
| P0-07 | Scheme name in config does not match Groww page title | Document mapping table; eval uses canonical `scheme_name` from config | Medium |

## Scope & compliance rules

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P0-08 | Compliance doc allows “cite AMFI when unsure” | Remove; policy must require closed five URLs or not-found | Critical |
| P0-09 | Eval golden set includes facts not on any Groww page (e.g. SID clause text) | Remove or mark `expected: not_found`; do not expand corpus | High |
| P0-10 | Eval expects citation to `hdfcfund.com` | Update eval to one of five Groww URLs only | Critical |
| P0-11 | Golden set has no refusal/advisory cases | Add advisory prompts per problem statement before Phase 7 | High |
| P0-12 | Footer format undefined (date vs datetime) | Standardize in `complianceRules.md`: `Last updated from sources: YYYY-MM-DD` | Medium |
| P0-13 | “Max 3 sentences” undefined (bullet points, semicolons) | Define: split on `.` `!` `?`; footers/citation line excluded from count | Medium |

## Scheme mapping & ambiguity

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P0-14 | User query alias: “HDFC Tax Saver” vs “ELSS” | Map aliases in `config/scheme_aliases.yaml` to ELSS URL | Medium |
| P0-15 | “HDFC Equity” confused with “HDFC Focused” | Aliases must not overlap; document disambiguation in eval | Medium |
| P0-16 | Query about “HDFC Flexi Cap” (not in corpus) | Eval expects out-of-scope / not-found; no new URL | High |
| P0-17 | Generic “HDFC fund” without scheme | Policy: clarify or use default citation rules (document in Phase 3/4) | Medium |

## Deliverables & handoff

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P0-18 | README lists 15–25 URLs (old problem statement wording) | README states exactly five URLs and closed-corpus limitation | High |
| P0-19 | Phase 1 starts before frozen `url_registry.csv` | Gate: Phase 0 exit checklist signed off in repo | Medium |
| P0-20 | `eval/golden_queries.jsonl` cites wrong scheme URL for a fact | Fix in Phase 0; each row has `expected_citation_url` ∈ closed set | High |

## Closed corpus policy violations (design time)

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P0-21 | Architecture doc or ticket proposes “add AMFI link for refusals” | Reject; refusals use one of five URLs per [architecture.md](../architecture.md) | Critical |
| P0-22 | Plan to follow outbound links from Groww pages to AMC PDFs | Reject; link blocker is a Phase 1 requirement | Critical |
| P0-23 | “Supplementary corpus” env flag | Must not exist; no feature flag to bypass allowlist | Critical |

---

## Test hints (Phase 0)

- Static test: `url_registry.csv` row count === 5 and every URL ∈ allowlist constant.
- Static test: all `expected_citation_url` in golden eval ∈ allowlist.
- Review checklist: `complianceRules.md` mentions closed corpus and refusal link constraint.
