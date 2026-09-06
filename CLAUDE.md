# CLAUDE.md

Read and follow [AGENTS.md](AGENTS.md) — it applies in full to every change
made in this repo.

The short version: any change to user-facing behavior must ship, in the same
commit, with (1) a new or amended entry in `docs/KEY_PRODUCT_FLOWS.md`
(including an accurate Test status line) and (2) the tests that entry claims
(pytest in `tests/`). Also: every push to `main` auto-deploys live to Google
Cloud Run (`https://americanlutheranchurchkellogg.com`).
