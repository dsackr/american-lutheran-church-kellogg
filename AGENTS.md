# Instructions for AI agents (and humans) working in this repo

These rules are binding for every change made in this repository, whether
authored by a human or an AI coding agent. `CLAUDE.md` points here; if your
tool reads a different instructions file, treat this one as authoritative.

## The two non-negotiables for feature work

Any change that adds or alters **user-facing behavior** — a new capability,
a new UI surface or action, a changed flow, a fixed behavioral bug — must
land in the same commit/PR with BOTH of the following. Neither is optional,
and neither may be deferred to "a follow-up":

1. **A Key Product Flows update.** `docs/KEY_PRODUCT_FLOWS.md` is the
   source of truth for what "the product doing its job" means. Either add
   a new KPF entry or amend the affected one(s), keeping every section
   accurate: the description, **Entry points** (file + function names / DOM IDs / endpoints),
   **If it silently breaks** (what the congregation, visitor, or pastor actually experiences), and
   **Test status** (which suites/files cover it now). New entries are
   appended with the next number — KPF numbers are stable identifiers
   referenced from code comments and test docstrings, so never renumber
   existing entries. If your change closes a documented Gap, say so; if it
   introduces one, document the Gap honestly rather than omitting it.

2. **Tests that exercise the feature.** Define what "this works" means for
   the flow and encode it:
   - **Support Ticket API** (`api/main.py`): Python pytest in `tests/test_api.py`.
   - **Discord AI Webmaster Bot & Agent** (`bot/tools.py`, `bot/agent.py`, `bot/github_client.py`): Python pytest in `tests/test_bot_tools.py`, `tests/test_bot_agent.py`.
   - **Website Integrity & Client UI** (`index.html`, `about.html`, `visit.html`, `ministries.html`, `sermons.html`, `give.html`, `js/main.js`): Python pytest in `tests/test_website_integrity.py`, `tests/test_js_logic.py`.
   - Run from the repo root: `python3 -m pytest`.
   - The KPF entry's **Test status** line and the tests you ship must
     agree — never claim coverage the suite doesn't actually have.

A pure refactor with no behavior change doesn't need a new KPF, but if it
moves entry points, update the KPF entries that name them. Docs-only and
CI-only changes are exempt.

Before finishing any task, re-read your diff and ask: "did user-facing
behavior change?" If yes and there's no KPF diff and no test diff alongside
it, the work is not done.

## Repo-specific rules that will bite you

- **Pushing to `main` triggers live deployment to Google Cloud Run** (`alc-kellogg` service in `alc-kellogg-production`, region `us-west1`). Pushing = publishing live to `https://americanlutheranchurchkellogg.com`.
- **Sole Authorized Repository**: The bot and API are strictly restricted to `dsackr/american-lutheran-church-kellogg` on branch `main`.
- **Worship Theology & Content Integrity**: Strictly Traditional Lutheran Liturgy, Historic Hymnody, and Faithful Scripture Preaching (Zero contemporary/praise band elements).
- **Form Routing**: All visitor inquiries, prayer requests, and visit plans must route directly to Pastor Craig Shorey at `Cdshorey@gmail.com`.
- **Church Identity**: Canonical location is `15 E Mullan Ave, Kellogg, ID 83837`; Sunday worship service is at **10:00 AM**.
- **Native `<dialog>` Modals**: Modals in HTML must use standard `<dialog>` tags with `.showModal()`, backdrop click dismissal, and accessible ARIA attributes.
- **Run tests from repo root**: Run `python3 -m pytest tests/` from the repository root.

## Where things are documented

- `docs/KEY_PRODUCT_FLOWS.md` — the KPF catalog (read it before changing
  behavior; your change almost certainly touches one).
- `docs/TEST_LEDGER.md` — the durable, append-only record of test runs on
  `main`. CI appends rows automatically on push; if you run a suite by hand
  for a change that CI's path filters won't cover, append a `local` row
  yourself. Never rewrite or delete existing rows.
- `TESTING_STRATEGY.md` — the testing standard and phase/checkpoint tracker.
- `bot/README.md` — Discord AI Webmaster Bot architecture, Hermes 3 tool loop, and Discord setup.
- `setup-domains-dns.md` — Custom domain DNS records and SSL mapping.
