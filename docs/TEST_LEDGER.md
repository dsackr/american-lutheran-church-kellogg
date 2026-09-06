# Test Ledger

Append-only, durable record of test-suite runs against `main` and local development verifications. CI appends one row per suite per push (see the "Record result in the test ledger" step in `.github/workflows/tests.yaml`); rows are committed back to this file with `[skip ci]`, so recording never triggers more CI. Failures are recorded too — a red row is the point of having a ledger.

Notes on reading it:
- Both automated and manual runs record results here.
- `Coverage` is the overall test coverage percentage across Python backend modules (`api/` and `bot/`).
- Rows marked `local` were recorded manually before CI execution or during local feature verification.

| Date (UTC) | Commit | Suite | Result | Detail | Coverage | Source |
|---|---|---|---|---|---|---|
| 2026-08-22 | initial | full-suite | pass | 51 passed in 0.69s | 94% | local |
| 2026-09-06 | 7631d06 | full-suite | success | 51 passed in 1.86s | 78% | CI |
