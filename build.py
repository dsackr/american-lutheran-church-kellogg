#!/usr/bin/env python3
"""
Build script for American Lutheran Church Kellogg static site.

Stitches partials/ (header, footer, support-modal) into pages/*.src.html
using per-page variables from pages/manifest.json, and writes the final
static .html files to the repo root for the nginx/Cloud Run deploy.

Usage:
    python3 build.py            # build all pages
    python3 build.py --check    # build + verify no page changed (CI dry-run)

Why this exists: header/footer/support-ticket-modal markup used to be
copy-pasted into all 6 page files. That caused real bugs (see GitHub issue
#14) where a fix applied to one page silently failed to propagate to the
other 5. This script is now the single source of truth for that shared
markup — edit partials/*.html, never edit the shared blocks directly in
the root .html files (they get overwritten on the next build).
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
PARTIALS = REPO / "partials"
PAGES = REPO / "pages"

PAGE_NAMES = ["index", "about", "sermons", "ministries", "visit", "give"]


def load_partial(name: str) -> str:
    return (PARTIALS / f"{name}.html").read_text(encoding="utf-8")


def render_header(active_page: str, has_mobile_call_cta: bool, has_banner_aria_label: bool) -> str:
    tpl = load_partial("header")
    for pg in PAGE_NAMES:
        token = f"{{{{ACTIVE_{pg.upper()}}}}}"
        tpl = tpl.replace(token, " active" if pg == active_page else "")
    call_cta = (
        '<a href="tel:2087867791" class="btn btn-outline-white">Call (208) 786-7791</a>'
        if has_mobile_call_cta
        else ""
    )
    tpl = tpl.replace("{{MOBILE_CALL_CTA}}", call_cta)
    # Clean up an empty line left behind when call_cta is blank
    if not has_mobile_call_cta:
        tpl = tpl.replace("      \n", "", 1)
    aria = ' aria-label="Church announcements and quick contact"' if has_banner_aria_label else ""
    tpl = tpl.replace("{{BANNER_ARIA_LABEL}}", aria)
    return tpl


def render_support_modal(page_name: str, ticket_placeholder: str) -> str:
    tpl = load_partial("support-modal")
    tpl = tpl.replace("{{TICKET_PAGE}}", f"{page_name}.html")
    tpl = tpl.replace("{{TICKET_PLACEHOLDER}}", ticket_placeholder)
    return tpl


def render_footer() -> str:
    return load_partial("footer")


def build_page(page_name: str, meta: dict) -> str:
    src = (PAGES / f"{page_name}.src.html").read_text(encoding="utf-8")
    src = src.replace("<!--#include header-->", render_header(meta["active_page"], meta["has_mobile_call_cta"], meta["has_banner_aria_label"]))
    src = src.replace("<!--#include footer-->", render_footer())
    src = src.replace(
        "<!--#include support-modal-->",
        render_support_modal(meta["active_page"], meta["ticket_placeholder"]),
    )
    if "<!--#include" in src:
        raise RuntimeError(f"{page_name}: unresolved include marker left in output")
    return src


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if build output would change any tracked file")
    args = parser.parse_args()

    manifest = json.loads((PAGES / "manifest.json").read_text(encoding="utf-8"))

    changed = []
    for page_name, meta in manifest.items():
        output = build_page(page_name, meta)
        out_path = REPO / f"{page_name}.html"
        existing = out_path.read_text(encoding="utf-8") if out_path.exists() else None
        if existing == output:
            print(f"  {page_name}.html: unchanged")
            continue
        changed.append(page_name)
        if args.check:
            print(f"  {page_name}.html: WOULD CHANGE", file=sys.stderr)
        else:
            out_path.write_text(output, encoding="utf-8")
            print(f"  {page_name}.html: written")

    if args.check and changed:
        print(f"\nFAIL: {len(changed)} page(s) out of date with partials: {', '.join(changed)}", file=sys.stderr)
        print("Run `python3 build.py` and commit the result.", file=sys.stderr)
        sys.exit(1)

    print("\nBuild complete." if not args.check else "\nCheck passed: all pages up to date.")


if __name__ == "__main__":
    main()
