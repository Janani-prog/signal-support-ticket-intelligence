# Security & Access Document
## Signal — Support Ticket Intelligence Platform

**Status:** Shipped — v1.0
**Scope note:** This is a free, portfolio-scale deployment, not a production system handling
real customer data. Controls below are scoped accordingly — proportionate, not theatrical.

---

## 1. Data Handling

- **No real PII, ever.** Only public datasets (`banking77`, Twitter Customer Support dataset, or
  similar) or synthetic data are used. This must be stated explicitly in the README.
- If any dataset used turns out to contain incidentally-identifying information (e.g. real
  usernames in a scraped dataset), scrub or hash user identifiers before ingestion.
- No raw data committed to git — data lives in `data/` and is gitignored; ingestion scripts
  document how to regenerate it from the public source.

---

## 2. Secrets Management

- No API keys are required for the default build (all models are local/open-source). If a
  future extension adds a hosted API (e.g. a hosted LLM for better summarization), keys must:
  - Never be hardcoded or committed.
  - Be loaded from environment variables (`.env`, gitignored) or the hosting platform's secret
    manager (HF Spaces secrets, Streamlit secrets.toml — also gitignored).
- `.env.example` should be committed with placeholder keys/names so the setup is reproducible
  without exposing real values.

---

## 3. Application Security (API layer)

- **CORS:** restrict allowed origins to the deployed frontend's actual domain in production;
  permissive (`*`) only acceptable for local dev.
- **Input validation:** FastAPI/Pydantic models validate all request bodies — reject malformed
  input rather than passing it straight to models (basic robustness, also prevents trivial
  crash-the-demo issues).
- **Rate limiting:** lightweight rate limiting on `/ask` and `/classify` (e.g. `slowapi`, free)
  to prevent the free-tier hosting quota from being exhausted by accidental loops or abuse —
  practical necessity given the $0 budget, not just a security nicety.
- **No user-generated content is executed** — ticket text is only ever treated as data (embedded,
  classified, summarized), never interpolated into shell commands, file paths, or eval'd code.
  Explicitly avoid any prompt-injection-adjacent risk if a hosted LLM is added later: treat
  retrieved ticket text as untrusted content within any future LLM prompt, not as instructions.

---

## 4. Access Control

- **Default: public demo, read-only.** No login required to view the dashboard or ask
  questions — appropriate since there's no real user data at stake and the goal is a
  frictionless, recruiter-friendly demo.
- **Optional lightweight gate:** if you want to prevent random internet traffic from exhausting
  free-tier compute, a simple shared password (Streamlit's `st.secrets` + a basic check, or HF
  Spaces' built-in private/public toggle) is sufficient — no need for full auth/OAuth for this
  project's purpose.
- If a write path is ever added (e.g. a human correcting a classification), that path should
  require the same lightweight gate at minimum, since it mutates logged data.

---

## 5. Dependency & Infrastructure Hygiene

- Pin dependency versions in `requirements.txt`.
- Run `pip-audit` (free) before deployment to catch known-vulnerable packages — cheap, and a
  good habit to mention in the README as a signal of security awareness.
- Docker image should run as a non-root user.
- HTTPS is handled automatically by the free hosting platforms (HF Spaces / Streamlit Community
  Cloud) — no manual TLS config needed for this deployment, but note in the architecture doc
  that this would need explicit handling on self-managed infrastructure.

---

## 6. Threat Model (stated explicitly, portfolio scale)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Free-tier compute abuse (scraping/looping the demo) | Medium | Low (quota/downtime, no data risk) | Rate limiting, optional access gate |
| Dependency vulnerability | Low | Low | `pip-audit`, pinned versions |
| Accidental PII in dataset | Low | Medium (reputational, not legal at this scale) | Public-dataset-only policy, scrub step |
| Prompt injection via ticket text (if hosted LLM added later) | Low (v1 has no hosted LLM) | Low–Medium | Treat retrieved text as data not instructions |

This table should be revisited and expanded if the project is ever extended toward handling
real user data or adding write/auth paths.
