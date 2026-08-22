# Key Product Flows — American Lutheran Church Kellogg Website

This document describes the site's key end-to-end user/data flows and the
files involved in each, so a change to any one flow can be traced across
the full stack (static HTML → JS → Cloud Run API → GitHub → ALC Support
agent).

## 1. Static Site Build (Header / Footer / Support Modal)

**Problem it solves:** Prior to this system, `header`, `footer`, and the
website-support-ticket `<dialog>` modal were copy-pasted verbatim into all
6 page files (`index.html`, `about.html`, `sermons.html`, `ministries.html`,
`visit.html`, `give.html`). A fix applied to one page (e.g. give.html)
silently failed to propagate to the other 5 — see GitHub issue #14, where
the support form's "Pastor Craig" / "Cdshorey@gmail.com" placeholders were
fixed on give.html but stayed live on 5 other pages for over a day.

**How it works now:**
- `partials/header.html`, `partials/footer.html`, `partials/support-modal.html`
  hold the single source of truth for shared markup, with `{{TOKEN}}`
  placeholders for the handful of legitimate per-page differences
  (active nav link, index.html's extra mobile "Call" button, index.html's
  banner `aria-label`, and the per-page "Example: ..." ticket placeholder
  hint text).
- `pages/<name>.src.html` is each page's full markup with the shared
  blocks replaced by `<!--#include header-->` / `<!--#include footer-->` /
  `<!--#include support-modal-->` markers.
- `pages/manifest.json` holds the per-page variables (`active_page`,
  `ticket_placeholder`, `has_mobile_call_cta`, `has_banner_aria_label`).
- `build.py` reads `pages/*.src.html` + `partials/*.html` + `manifest.json`
  and writes the final static `index.html`, `about.html`, etc. to the repo
  root — these are what nginx/Cloud Run actually serves.

**Workflow for any change to header, footer, or the support ticket modal:**
1. Edit the relevant file under `partials/`.
2. Run `python3 build.py` from the repo root. This overwrites the 6 root
   `.html` files.
3. Run `python3 test_build.py` to verify (should be zero failures).
4. `git add` the changed partial(s) AND the regenerated root `.html` files
   together in the same commit, then push.

**Workflow for any change to page-specific content** (hero text, ministry
cards, sermon embed, etc.): edit the relevant `pages/<name>.src.html` file
directly (not the root `.html` — it will be overwritten on the next
`build.py` run), then run `python3 build.py` and commit both.

**CI enforcement:** `.github/workflows/deploy.yml` runs
`python3 build.py --check` before every deploy. If a root `.html` file was
hand-edited and no longer matches what `partials/` + `manifest.json`
would produce, the build fails loudly instead of silently deploying stale
or drifted markup.

**Files:**
- `partials/header.html`, `partials/footer.html`, `partials/support-modal.html`
- `pages/*.src.html`, `pages/manifest.json`
- `build.py`, `test_build.py`

## 2. Website Support Ticket Flow

**User-facing entry point:** "🛠️ Website Support" link in the footer of
every page, opens the `#support-modal` dialog (see Flow 1 above for how
that modal is kept in sync across pages).

**Data path:**
1. Visitor fills out the form (`js/main.js` handles the `#support-form`
   submit event) → `fetch('/api/support-ticket', ...)`.
2. `nginx.conf` proxies `/api/support-ticket` to the serverless Cloud Run
   service `alc-support-ticket` (source: `api/main.py`, `api/Dockerfile`,
   deployed separately from the main site).
3. That service creates a GitHub Issue on
   `dsackr/american-lutheran-church-kellogg` with a structured body
   (page name, target URL, target file, submitter, timestamp, description).
4. The ALC Support agent (this Hermes profile) picks up new issues via the
   hourly `alc-hourly-tickets` cron job, evaluates them against the
   7-step workflow, and — after Dale's Discord approval — edits the
   target file, commits, pushes, and closes the issue once verified live.

**Files:** `partials/support-modal.html` (form markup), `js/main.js`
(submit handler), `nginx.conf` (`/api/support-ticket` proxy), `api/main.py`
(ticket → GitHub Issue backend).

## 3. Plan Your Visit / Prayer Request Flows

Two other modals exist per-page: `#visit-modal` and `#prayer-modal`.
**Note:** unlike the support-modal, these currently have real per-page
content differences (different intro copy, different field sets — e.g.
`ministries.html`'s visit modal is repurposed as a Sunday School
registration form with different labels). They were intentionally left
page-specific rather than forced into a shared partial during the August
2026 refactor, since the content genuinely differs by page rather than
being an accidental copy-paste bug. If a future ticket asks to make these
consistent across pages, that's a deliberate content decision — bring it
to Dale for approval before consolidating, since it changes visible page
behavior, not just deduplicates identical markup.

**Files:** inline in each `pages/<name>.src.html` (footer/`data-open-visit`
and `data-open-prayer` triggers live in the header partial; the modal
bodies live in the individual page's own markup, currently NOT extracted).

## 4. Deploy Pipeline

`git push origin main` → GitHub Actions (`.github/workflows/deploy.yml`)
→ `python3 build.py --check` (fails fast if partials/manifest drifted from
committed root `.html`) → `python3 test_build.py` → `gcloud run deploy` →
live on Cloud Run (`alc-kellogg`, `us-west1`) behind the HTTPS Load
Balancer at `americanlutheranchurchkellogg.com` (~55s end to end).
