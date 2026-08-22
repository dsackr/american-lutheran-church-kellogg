#!/usr/bin/env python3
"""
Structural tests for the ALC Kellogg static site build system.

Run with: python3 test_build.py
Exits non-zero on any failure (safe to wire into CI).

These tests exist because of GitHub issue #14: a fix applied to give.html's
support-ticket-modal placeholders did not propagate to the other 5 pages,
because the header/footer/support-modal markup used to be copy-pasted per
page. The partials + build.py system (see kpf.md, "Website Support Ticket
Flow") replaced that copy-paste with a single source of truth. These tests
guard against that regression class recurring.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
PAGE_NAMES = ["index", "about", "sermons", "ministries", "visit", "give"]

failures = []


def check(condition: bool, description: str):
    if condition:
        print(f"  PASS  {description}")
    else:
        print(f"  FAIL  {description}")
        failures.append(description)


def read(page: str) -> str:
    return (REPO / f"{page}.html").read_text(encoding="utf-8")


def test_build_is_deterministic_and_committed():
    """build.py --check must pass: committed .html files must match what
    the partials + manifest currently produce. If this fails, someone
    edited a root .html file directly instead of editing partials/ and
    rerunning build.py, or forgot to run build.py after editing a partial."""
    import subprocess

    result = subprocess.run(
        [sys.executable, str(REPO / "build.py"), "--check"],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    check(result.returncode == 0, "build.py --check passes (root .html files match partials/manifest)")
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)


def test_support_ticket_placeholders_no_pastor_reference():
    """Regression test for issue #14: the support ticket form's name/email
    fields must never default to Pastor Craig's name or personal email —
    they should be generic ('Your Name', 'your@email.com or phone number')
    on every single page."""
    for page in PAGE_NAMES:
        html = read(page)
        has_name_field = 'id="ticket-name"' in html
        has_contact_field = 'id="ticket-contact"' in html
        check(has_name_field and has_contact_field, f"{page}.html: support form has ticket-name and ticket-contact fields")

        no_pastor_name = "Pastor Craig / Church Member" not in html
        no_pastor_email_placeholder = 'placeholder="Cdshorey@gmail.com' not in html
        check(no_pastor_name, f"{page}.html: ticket-name placeholder does not reference Pastor Craig")
        check(no_pastor_email_placeholder, f"{page}.html: ticket-contact placeholder does not reference Cdshorey@gmail.com")


def test_support_modal_identical_structure_across_pages():
    """The support-ticket <dialog> markup (fields, labels, buttons) must be
    structurally identical across all 6 pages -- only the current-page name
    and the example placeholder text may differ."""
    modals = {}
    for page in PAGE_NAMES:
        html = read(page)
        m = re.search(r"<dialog id=\"support-modal\".*?</dialog>", html, re.DOTALL)
        check(m is not None, f"{page}.html: support-modal dialog found")
        if m:
            modals[page] = m.group(0)

    def normalize(block: str) -> str:
        block = re.sub(r'(<span id="ticket-page-display">)[^<]*(</span>)', r"\1PAGE\2", block)
        block = re.sub(r'(placeholder=")Example:[^"]*(")', r"\1EXAMPLE\2", block)
        return block

    if modals:
        baseline = normalize(modals[PAGE_NAMES[0]])
        for page in PAGE_NAMES[1:]:
            check(
                normalize(modals[page]) == baseline,
                f"{page}.html: support-modal structurally identical to {PAGE_NAMES[0]}.html",
            )


def test_footer_byte_identical_across_pages():
    """The <footer> block must be byte-identical on every page. There is no
    per-page footer content, so any drift here is a bug."""
    footers = {}
    for page in PAGE_NAMES:
        html = read(page)
        m = re.search(r"<!-- Site Footer -->.*?</footer>", html, re.DOTALL)
        check(m is not None, f"{page}.html: footer block found")
        if m:
            footers[page] = m.group(0)

    if footers:
        baseline = footers[PAGE_NAMES[0]]
        for page in PAGE_NAMES[1:]:
            check(footers[page] == baseline, f"{page}.html: footer byte-identical to {PAGE_NAMES[0]}.html")


def test_active_nav_matches_current_page():
    """Each page's desktop + mobile nav must mark exactly its own link
    'active', and no other page's link, in both the desktop nav and the
    mobile drawer menu."""
    labels = {
        "index": "Home",
        "about": "About Us",
        "sermons": "Sermons & Media",
        "ministries": "Ministries",
        "visit": "Plan Your Visit",
        "give": "Give",
    }
    for page in PAGE_NAMES:
        html = read(page)
        for other in PAGE_NAMES:
            label = labels[other]
            desktop_active = f'<a href="{other}.html" class="nav-link active">{label}</a>' in html
            mobile_active = f'<a href="{other}.html" class="mobile-nav-link active">{label}' in html
            if other == page:
                check(desktop_active, f"{page}.html: desktop nav marks '{label}' active")
                check(mobile_active, f"{page}.html: mobile nav marks '{label}' active")
            else:
                check(not desktop_active, f"{page}.html: desktop nav does NOT mark '{label}' active")
                check(not mobile_active, f"{page}.html: mobile nav does NOT mark '{label}' active")


def test_manifest_covers_all_pages():
    manifest = json.loads((REPO / "pages" / "manifest.json").read_text(encoding="utf-8"))
    check(set(manifest.keys()) == set(PAGE_NAMES), "manifest.json has an entry for every page, no extras")


def main():
    print("=== build determinism ===")
    test_build_is_deterministic_and_committed()
    print("=== manifest coverage ===")
    test_manifest_covers_all_pages()
    print("=== support ticket form (regression: issue #14) ===")
    test_support_ticket_placeholders_no_pastor_reference()
    print("=== support modal structural parity ===")
    test_support_modal_identical_structure_across_pages()
    print("=== footer parity ===")
    test_footer_byte_identical_across_pages()
    print("=== active nav correctness ===")
    test_active_nav_matches_current_page()

    print()
    if failures:
        print(f"FAILED: {len(failures)} check(s) failed")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("All checks passed.")


if __name__ == "__main__":
    main()
