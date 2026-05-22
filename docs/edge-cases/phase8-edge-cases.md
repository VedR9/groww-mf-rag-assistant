# Phase 8 Edge Cases: Deployment, Operations & Documentation

**Architecture reference:** [Phase 8](../architecture.md#phase-8-deployment-operations--documentation)

---

## Packaging & setup

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P8-01 | `.env` not copied; API key missing | `.env.example` documents vars; startup error names missing key | High |
| P8-02 | README setup steps omit ingest step | Document: ingest five URLs → index → run API → UI | High |
| P8-03 | `requirements.txt` pins no versions | Pin major versions for reproducible demos | Medium |
| P8-04 | Docker image builds without corpus | Volume mount or build-time ingest documented | High |
| P8-05 | Wrong Python version (3.9) | README states 3.11+; version check in CLI | Medium |
| P8-06 | Committed `.env` with real API key | `.gitignore`; secret scan in CI | Critical |

## Corpus refresh job

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P8-07 | Cron re-fetches sixth URL from bad config | Job validates registry === 5 before fetch | Critical |
| P8-08 | Refresh succeeds but re-embed not triggered | Pipeline: hash change → Phase 2 → Phase 3 | High |
| P8-09 | Refresh during active demo | Read-only index swap or brief 503 | Medium |
| P8-10 | All five fetches fail (Groww outage) | Keep last good index; alert ops | High |
| P8-11 | Partial refresh (1 scheme updated) | Mixed `fetched_at` in footer—use per-chunk dates | Medium |
| P8-12 | Manual refresh script accepts URL argument | Reject args not in allowlist | Critical |

## Monitoring & health

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P8-13 | `/health` OK but vector index empty | Deep health: `chunk_count >= 1` | Critical |
| P8-14 | Logs contain full chat messages with PII | Log `query_hash`, intent, refusal flag only | Critical |
| P8-15 | Logs contain API keys on error stack | Redact secrets in logging middleware | Critical |
| P8-16 | No alert on spike in refusals | Informational metric only; not PII | Low |
| P8-17 | No alert on retrieval score drop | Optional anomaly log after refresh | Low |
| P8-18 | Disk fills with raw HTML versions | Retention policy: keep last N versions per scheme | Medium |

## Documentation & limitations

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P8-19 | README claims AMFI/SEBI sources | Correct to five Groww URLs only | Critical |
| P8-20 | Known limitations omit closed corpus | State: only five pages; missing facts unanswerable | High |
| P8-21 | Known limitations omit JS-render risk | Document if Groww pages are CSR-heavy | Medium |
| P8-22 | Disclaimer missing from README snippet | Include exact problem-statement disclaimer | High |
| P8-23 | Architecture link broken in README | Link to `docs/architecture.md` | Low |
| P8-24 | Edge-case docs not linked | Link `docs/edge-cases/README.md` from README | Low |

## Deployment environments

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P8-25 | Production UI points to localhost API | Env-specific `VITE_API_URL` / proxy | High |
| P8-26 | CORS `*` in production | Restrict to deployed UI origin | High |
| P8-27 | Admin `/ingest` exposed publicly | Protect or disable in prod | Critical |
| P8-28 | Rate limiting absent on `/chat` | Basic IP rate limit to control LLM cost | Medium |
| P8-29 | Cold start loads index on first query | Preload index at process start | Medium |
| P8-30 | Multi-worker API without shared index | Each worker loads index or use shared vector service | Medium |

## Handoff & maintenance

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P8-31 | New developer runs chat without ingest | Clear error: index not found | High |
| P8-32 | Groww changes URL slugs (404) | Manual update to Phase 0 allowlist—no auto-discovery | High |
| P8-33 | Scheme renamed on Groww page | Update `scheme_name` in config; re-eval golden | Medium |
| P8-34 | Project archived; live URLs rot | Pin last successful raw HTML in repo for demo | Low |
| P8-35 | Dependency CVE in parser lib | Document upgrade path; minimal deps | Medium |

---

## Test hints (Phase 8)

- Fresh clone drill: follow README only; chat returns cited answer in &lt; 30 minutes.
- Run refresh twice; assert request count === 5 per run.
- Hit `/health` with empty `data/processed/` → unhealthy.
