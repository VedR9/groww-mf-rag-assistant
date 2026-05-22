# Phase 1 Edge Cases: Corpus Definition & Acquisition

**Architecture reference:** [Phase 1](../architecture.md#phase-1-corpus-definition--acquisition)  
**Input:** Five closed Groww URLs only.

---

## URL registry loader

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P1-01 | Registry file empty | Abort ingest; log error | Critical |
| P1-02 | Registry has valid fifth URL with UTF-8 BOM | Strip BOM; load succeeds | Medium |
| P1-03 | Extra column with external PDF link in CSV | Ignore column or fail if any cell contains non-allowlisted URL | Critical |
| P1-04 | URL with query params (`?utm_source=...`) | Normalize to canonical path or reject if not in allowlist | High |
| P1-05 | Allowlist implemented as substring `groww.in` | Reject `https://groww.in/blog/...`—must match exact five paths | Critical |

## Fetcher & network

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P1-06 | HTTP 403/401 from Groww | Retry with backoff; mark scheme failed in provenance; do not substitute URL | High |
| P1-07 | HTTP 404 for one scheme URL | Ingest partial success (4/5); health report lists failed slug; no alternate URL | High |
| P1-08 | Timeout on single URL | Retry N times; record failure; other four still stored | High |
| P1-09 | Rate limit (429) | Exponential backoff; respect `Retry-After` if present | Medium |
| P1-10 | Redirect 302 to non-allowlisted domain | Do not follow; fail fetch for that URL | Critical |
| P1-11 | Redirect 302 to another allowlisted scheme URL | Do not follow redirects (or only if final URL still in allowlist) | High |
| P1-12 | Response is JSON/API payload instead of HTML | Log content-type mismatch; fail or flag for manual review | High |
| P1-13 | Response body &lt; 1 KB (error/empty page) | Flag `suspiciously_small`; do not index until resolved | High |
| P1-14 | gzip/br encoding | Decode correctly; store uncompressed HTML | Medium |
| P1-15 | TLS/certificate errors | Fail fetch; do not disable cert verification in prod | High |

## Link blocker & crawl scope

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P1-16 | HTML contains AMC factsheet PDF links | Do not fetch PDFs; store HTML only | Critical |
| P1-17 | HTML contains links to other Groww funds (sixth scheme) | Do not fetch; no additional index entries | Critical |
| P1-18 | `robots.txt` disallows user-agent | Log warning; respect robots; document manual fetch policy if blocked | Medium |
| P1-19 | Inline images/scripts from CDN | Ignore for corpus text; no CDN crawl | Low |
| P1-20 | `sitemap.xml` discovery attempted | Disable; only five explicit GETs | Medium |

## Provenance & versioning

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P1-21 | Re-fetch: content unchanged (`content_hash` same) | Update `fetched_at` only; skip re-chunk if downstream hooks content hash | Medium |
| P1-22 | Re-fetch: page layout changed, hash different | New raw artifact version; trigger Phase 2 re-process | High |
| P1-23 | Concurrent ingest jobs | File lock or idempotent writes per `scheme_slug` | Medium |
| P1-24 | Disk full while saving raw HTML | Fail atomically; no partial file without marker | High |
| P1-25 | Clock skew on `fetched_at` | Use UTC ISO8601 consistently | Low |

## Security & privacy (ingest)

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P1-26 | Accidental ingest of URL containing credentials in path | Reject; never log full secrets | Critical |
| P1-27 | HTML contains sample PAN/Aadhaar in comments | Strip in Phase 2; do not echo in logs | High |

---

## Test hints (Phase 1)

- Mock HTTP: 404 on one URL → exactly four artifacts, provenance shows one failure.
- Assert network layer never requests host outside `groww.in` or path outside allowlist.
- Integration: full ingest produces five raw folders or documented partial failure.
