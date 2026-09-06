# Testing Strategy

Status: Living document. Tracks how this repository tests its Key Product Flows
(see [docs/KEY_PRODUCT_FLOWS.md](docs/KEY_PRODUCT_FLOWS.md)) and what remains to be covered.

## 1. Why this exists

The American Lutheran Church platform combines static responsive web interfaces, an automated Support Ticket REST API (`api/`), a Discord AI Webmaster Bot (`bot/`), and Cloud Run automated deployment pipelines.

This document records the testing standard this project holds itself to, and provides future contributors (human or AI) with clear guidelines and a checkpoint tracker rather than a from-scratch decision whenever coverage or new features are introduced.

## 2. Tooling & Strategy

- **Test Framework**: `pytest` + `pytest-cov` for testing Python modules, API endpoints, bot tool pipelines, HTML semantic structure, and client-side JavaScript algorithms.
- **Suite Organization**:
  - `tests/test_api.py`: Comprehensive test suite for `api/main.py` (CORS handling, health checks, issue payload generation, target file resolution, error handling).
  - `tests/test_bot_tools.py`: Tests for `bot/tools.py` (safe file listing, whitelist filtering, unified diff generation, PIL image resizing and compression).
  - `tests/test_bot_agent.py`: Tests for `bot/agent.py` and `bot/github_client.py` (strict operational boundary enforcement, Hermes 3 tool loop parsing, mock GitHub API interactions).
  - `tests/test_website_integrity.py`: Structural DOM validation of all HTML pages (`index.html`, `about.html`, `visit.html`, `ministries.html`, `sermons.html`, `give.html`), verifying navigation links, modal tags, form field attributes, canonical address consistency, pastor email routing, and service times.
  - `tests/test_js_logic.py`: Unit tests for client-side JavaScript logic (Sunday 10:00 AM countdown algorithm, URL-to-filename deduction, form payload structures).
  - `tests/conftest.py`: Shared fixtures, simulated repo directories, and HTTP mocks.
- **Running Tests Locally**:
  ```bash
  python3 -m pytest tests/ -v --cov=api --cov=bot --cov-report=term-missing
  ```

## 3. Where Test Results Live

- **Durable In-Repo Record**: [docs/TEST_LEDGER.md](docs/TEST_LEDGER.md) — an append-only ledger of test suite runs on `main` and verified local runs. CI appends a row (date, commit, suite, result, counts, coverage) on push runs, committed back with `[skip ci]`.
- **CI Workflow**: `.github/workflows/tests.yaml` runs the test suite on every push and pull request, writes a coverage report to the GitHub Actions job summary, and records passing/failing runs to `docs/TEST_LEDGER.md`.
- **Deployment Pipeline**: `.github/workflows/deploy.yml` triggers Google Cloud Run builds on push to `main`.

## 4. Post-Deployment Smoke Testing

`scripts/smoke_test.py` exercises the live website and API endpoints against the production site `https://americanlutheranchurchkellogg.com` or a local development container.

To run the smoke test:
```bash
# Against production
python3 scripts/smoke_test.py

# Against local dev instance
python3 scripts/smoke_test.py --url http://localhost:8080
```

The smoke test validates:
- HTTP 200 and correct `Content-Type` on all HTML pages (`/`, `about.html`, `visit.html`, `ministries.html`, `sermons.html`, `give.html`).
- HTTP 200 on `/health` and static assets (`/css/styles.css`, `/js/main.js`, `/assets/icons/logo.svg`).
- Security headers (`X-Frame-Options`, `X-Content-Type-Options`, `Content-Security-Policy`).
- API CORS response headers for authorized origins.

## 5. Security & Load Testing

- **Security Isolation**:
  - `bot/tools.py` enforces `EDITABLE_EXTENSIONS` whitelist (`.html`, `.css`, `.js`, `.json`, `.xml`, `.txt`, `.md`) and ignores `.git/` and `bot/` configuration files.
  - `bot/agent.py` enforces single authorized repository boundaries (`dsackr/american-lutheran-church-kellogg` on `main`).
  - Discord commands verify `AUTHORIZED_USER_IDS` whitelist before executing file commits or deployments.
- **Static Analysis & Linters**:
  - Python tests ensure syntax validity of `nginx.conf`, `Dockerfile`, and HTML templates.

## 6. Coverage Target

Declared baseline targets across modules:

| Module / Component | Target Coverage | Scope |
|---|---|---|
| `api/main.py` | > 90% | Health, CORS, support ticket submission, error branches |
| `bot/tools.py` | > 90% | File listing, reading, diff generation, image optimization |
| `bot/agent.py` | > 80% | System prompt boundaries, tool loop parsing |
| `bot/github_client.py` | > 80% | File CRUD, image uploads, workflow run checks |
| Website Integrity & UI | 100% of pages | Links, modals, address, email, countdown, forms |

## 7. Phase Checkpoint Tracker

Maps to [docs/KEY_PRODUCT_FLOWS.md](docs/KEY_PRODUCT_FLOWS.md)'s numbered flows.

| Phase | Scope | KPFs | Status |
|---|---|---|---|
| 0 | Pytest infra: `pyproject.toml`, `requirements-test.txt`, `conftest.py`, CI workflow, Test Ledger | — | **Done** |
| 1 | Website Integrity: DOM validation, link checking, form field attributes, canonical address, service times | 1, 2, 3, 4, 5, 7, 8 | **Done** |
| 2 | Client JS Logic: Sunday 10am countdown math, path deduction, modal triggers | 1, 5, 6 | **Done** |
| 3 | Support Ticket API: Healthcheck, CORS, issue markdown formatter, GitHub REST API client | 6 | **Done** |
| 4 | Discord AI Bot: File tools, diff generator, image optimizer, Hermes 3 tool loop, GitHub client | 9 | **Done** |
| 5 | Live Smoke Test Script & Infrastructure verification: Cloud Run health checks, headers, static assets | 10 | **Done** |
