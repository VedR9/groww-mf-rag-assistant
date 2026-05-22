# Phase 6 Edge Cases: User Interface (Minimal)

**Architecture reference:** [Phase 6](../architecture.md#phase-6-user-interface-minimal)

---

## Welcome, disclaimer & examples

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P6-01 | Disclaimer scrolled out of view on mobile | Sticky footer or persistent banner: “Facts-only. No investment advice.” | High |
| P6-02 | User refreshes page | Disclaimer and welcome visible again | Medium |
| P6-03 | Example chip clicked | Populates input and sends (or fills only—document UX) | Medium |
| P6-04 | Example asks fact not on corpus (e.g. “download statement”) | Show not-found/refusal from API; chip still valid demo | High |
| P6-05 | Three examples all target same scheme | Prefer diversity across schemes/categories in copy | Low |
| P6-06 | Disclaimer text edited in UI only (not README) | Single source of truth from config constant | Low |

## Chat interaction

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P6-07 | User sends empty message | Disable send or inline validation | High |
| P6-08 | User spams send while loading | Disable input until response completes | Medium |
| P6-09 | Very long paste in input | Max length client-side; API 400 if exceeded | Medium |
| P6-10 | XSS in user message (`<script>`) | Escape on render; never `dangerouslySetInnerHTML` | Critical |
| P6-11 | XSS in API `answer` field | Escape; treat as text | Critical |
| P6-12 | Markdown in answer breaks layout | Safe subset or plain text | Medium |
| P6-13 | Citation URL `javascript:` scheme | Reject render; only `https://groww.in/...` allowlisted paths | Critical |
| P6-14 | Citation opens in new tab | `rel="noopener noreferrer"` on external link | Low |

## API contract & errors

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P6-15 | API returns 500 | Show error state; no fake answer | High |
| P6-16 | API timeout (30s+) | Loading → timeout message; retry option | High |
| P6-17 | API returns `refused: true` | Distinct styling (e.g. muted panel), not same as factual | Medium |
| P6-18 | API returns `citation_url` outside allowlist | UI should not link; log dev error (defense in depth) | Critical |
| P6-19 | Missing `footer` in JSON | Show answer but dev warning; prefer required field in OpenAPI | Medium |
| P6-20 | CORS blocked (local dev) | Document proxy or allowed origins in README | Medium |
| P6-21 | Wrong API base URL in build | Health check fails visibly on startup | Medium |

## Response display

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P6-22 | Answer + footer duplicated in UI | Render `answer` and `footer` once each per contract | Medium |
| P6-23 | URL not clickable (plain text) | Single clickable citation link | High |
| P6-24 | Multi-turn conversation | Show history; each turn shows its citation (if supported) | Low |
| P6-25 | Not-found message looks like error red | Use neutral informational styling | Low |
| P6-26 | Refusal looks like factual answer | Visual distinction + optional “Facts-only decline” label | Medium |

## Accessibility & layout

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P6-27 | Keyboard-only navigation | Send on Enter; focus management on response | Medium |
| P6-28 | Screen reader on citation | Announce “Source link” + scheme name | Low |
| P6-29 | Viewport 320px width | No horizontal scroll; disclaimer readable | Medium |
| P6-30 | Dark mode (if supported) | Disclaimer contrast still WCAG AA | Low |

## Privacy (UI)

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P6-31 | Browser autofill suggests email on chat input | `autocomplete="off"` on sensitive fields | Medium |
| P6-32 | Chat history stored in localStorage with PII | Do not persist queries if PII risk; or no persistence | High |
| P6-33 | Analytics captures full query text | Disable or hash; no PII payloads | High |

---

## Test hints (Phase 6)

- E2E: disclaimer visible on load and after refresh.
- Click each example chip → response has one allowlisted URL.
- Inject malicious citation in mock API → link not rendered.
