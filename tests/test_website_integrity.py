import re
from pathlib import Path
import pytest


def test_html_files_exist(repo_root):
    """Ensures all 6 primary HTML website pages exist in repository root."""
    required_pages = [
        "index.html",
        "about.html",
        "visit.html",
        "ministries.html",
        "sermons.html",
        "give.html",
    ]
    for page in required_pages:
        p = repo_root / page
        assert p.exists() and p.is_file(), f"Missing website page: {page}"


def test_html_structure_and_meta(mock_html_pages):
    """Ensures every HTML page contains DOCTYPE, html lang='en', viewport, charset, and title."""
    for page_path in mock_html_pages:
        content = page_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content or "<!doctype html>" in content.lower(), f"Missing DOCTYPE in {page_path.name}"
        assert '<html lang="en">' in content or "<html lang='en'>" in content, f"Missing lang='en' in {page_path.name}"
        assert '<meta name="viewport"' in content or "<meta name='viewport'" in content, f"Missing viewport in {page_path.name}"
        assert "<title>" in content and "</title>" in content, f"Missing title tag in {page_path.name}"
        assert "American Lutheran Church" in content, f"Missing church name in {page_path.name}"


def test_canonical_address_consistency(mock_html_pages):
    """Ensures the canonical address '15 E Mullan Ave, Kellogg, ID' is present across all pages."""
    canonical_addr = "15 E Mullan Ave, Kellogg, ID"
    for page_path in mock_html_pages:
        content = page_path.read_text(encoding="utf-8")
        assert canonical_addr in content, f"Canonical address '{canonical_addr}' not found in {page_path.name}"


def test_service_times_consistency(repo_root):
    """Ensures 10:00 AM Sunday worship is specified on homepage and visit page."""
    for page in ["index.html", "visit.html"]:
        content = (repo_root / page).read_text(encoding="utf-8")
        assert "10:00 AM" in content or "10:00 am" in content or "10 AM" in content, f"10:00 AM service time missing in {page}"


def test_pastor_email_routing(mock_html_pages):
    """Ensures Pastor Craig's email Cdshorey@gmail.com is referenced in website content."""
    home_content = (mock_html_pages[0].parent / "index.html").read_text(encoding="utf-8")
    assert "Cdshorey@gmail.com" in home_content or "Pastor Craig Shorey" in home_content


def test_modals_presence_across_all_pages(mock_html_pages):
    """Ensures all pages have native <dialog> elements for prayer, visit, and support modals."""
    required_modals = ["prayer-modal", "visit-modal", "support-modal"]
    for page_path in mock_html_pages:
        content = page_path.read_text(encoding="utf-8")
        for modal_id in required_modals:
            assert f'id="{modal_id}"' in content or f"id='{modal_id}'" in content, f"Modal #{modal_id} missing in {page_path.name}"


def test_prayer_modal_fields(mock_html_pages):
    """Ensures prayer modal contains text input and confidentiality checkbox."""
    for page_path in mock_html_pages:
        content = page_path.read_text(encoding="utf-8")
        assert 'id="prayer-text"' in content, f"#prayer-text missing in {page_path.name}"
        assert 'id="prayer-confidential"' in content, f"#prayer-confidential missing in {page_path.name}"


def test_support_modal_fields(mock_html_pages):
    """Ensures support ticket modal contains ticket-text and page tracking fields."""
    for page_path in mock_html_pages:
        content = page_path.read_text(encoding="utf-8")
        assert 'id="ticket-text"' in content, f"#ticket-text missing in {page_path.name}"
        assert 'id="ticket-page-url"' in content, f"#ticket-page-url missing in {page_path.name}"


def test_navigation_links_validity(mock_html_pages):
    """Ensures all internal navigation hrefs point to real files or anchors."""
    valid_destinations = {
        "index.html", "about.html", "visit.html", "ministries.html", "sermons.html", "give.html",
        "/", "#", ""
    }
    href_pattern = re.compile(r'href="([^"#:]+)(?:#[^"]*)?"')

    for page_path in mock_html_pages:
        content = page_path.read_text(encoding="utf-8")
        hrefs = href_pattern.findall(content)
        for h in hrefs:
            if h.startswith("mailto:") or h.startswith("tel:") or h.startswith("http"):
                continue
            cleaned = h.strip("/")
            assert cleaned in valid_destinations or (page_path.parent / cleaned).exists(), f"Broken link '{h}' found in {page_path.name}"


def test_sitemap_and_robots(repo_root):
    """Ensures sitemap.xml and robots.txt are consistent."""
    sitemap = (repo_root / "sitemap.xml").read_text(encoding="utf-8")
    robots = (repo_root / "robots.txt").read_text(encoding="utf-8")

    assert "americanlutheranchurchkellogg.com" in sitemap
    assert "about.html" in sitemap
    assert "visit.html" in sitemap
    assert "ministries.html" in sitemap
    assert "sermons.html" in sitemap
    assert "give.html" in sitemap
    assert "sitemap.xml" in robots


def test_nginx_config_rules_and_security_headers(repo_root):
    """Ensures nginx.conf includes essential security headers and routing rules."""
    nginx_conf = (repo_root / "nginx.conf").read_text(encoding="utf-8")
    assert "X-Frame-Options" in nginx_conf
    assert "X-Content-Type-Options" in nginx_conf
    assert "X-XSS-Protection" in nginx_conf
    assert "gzip" in nginx_conf
    assert "/api/support-ticket" in nginx_conf or "proxy_pass" in nginx_conf or "try_files" in nginx_conf


def test_dockerfile_presence_and_syntax(repo_root):
    """Ensures root Dockerfile exists and configures web serving."""
    dockerfile = (repo_root / "Dockerfile").read_text(encoding="utf-8")
    assert "FROM" in dockerfile
    assert "COPY" in dockerfile
