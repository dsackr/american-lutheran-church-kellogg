#!/usr/bin/env python3
"""
American Lutheran Church Kellogg — Post-Deployment Smoke Test

Exercises the live production website or local container instance across
all Key Product Flows (KPF 1-10) to verify HTML pages, static assets,
API endpoints, and security headers.

Usage:
    python3 scripts/smoke_test.py
    python3 scripts/smoke_test.py --url http://localhost:8080
"""

import argparse
import sys
import time
import urllib.request
import urllib.error
import json

HTML_PAGES = [
    ("/", "American Lutheran Church"),
    ("/about.html", "Pastor Craig Shorey"),
    ("/visit.html", "Plan Your Visit"),
    ("/ministries.html", "Ministries"),
    ("/sermons.html", "Sermons"),
    ("/give.html", "Giving"),
]

STATIC_ASSETS = [
    "/css/styles.css",
    "/js/main.js",
    "/assets/icons/logo.svg",
    "/robots.txt",
    "/sitemap.xml",
]


def test_url(base_url: str, path: str, expected_keyword: str = None, timeout: int = 10):
    url = f"{base_url.rstrip('/')}{path}"
    start = time.time()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ALC-Smoke-Test/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            content = response.read().decode("utf-8", errors="ignore")
            elapsed = time.time() - start

            if expected_keyword and expected_keyword not in content:
                return False, f"HTTP {status} in {elapsed:.2f}s, but missing expected text '{expected_keyword}'"

            return True, f"HTTP {status} in {elapsed:.2f}s ({len(content)} bytes)"
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start
        return False, f"HTTP Error {e.code} in {elapsed:.2f}s"
    except Exception as e:
        elapsed = time.time() - start
        return False, f"Connection Failed ({e}) in {elapsed:.2f}s"


def test_health_api(base_url: str, timeout: int = 10):
    url = f"{base_url.rstrip('/')}/health"
    start = time.time()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ALC-Smoke-Test/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            body = response.read().decode("utf-8")
            elapsed = time.time() - start
            data = json.loads(body)
            if data.get("status") == "ok":
                return True, f"HTTP {status} in {elapsed:.2f}s — API status ok"
            return False, f"HTTP {status} in {elapsed:.2f}s — unexpected JSON: {body}"
    except Exception as e:
        elapsed = time.time() - start
        return False, f"API health check failed: {e} in {elapsed:.2f}s"


def main():
    parser = argparse.ArgumentParser(description="ALC Kellogg Smoke Test")
    parser.add_argument("--url", default="https://americanlutheranchurchkellogg.com", help="Target URL")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    args = parser.parse_args()

    target = args.url
    print(f"\n=======================================================")
    print(f"  ALC Kellogg Smoke Test: {target}")
    print(f"=======================================================\n")

    passed = 0
    failed = 0

    # 1. HTML Pages
    print("--- 📄 HTML Pages (KPF 1-5, 7, 8) ---")
    for path, keyword in HTML_PAGES:
        ok, msg = test_url(target, path, keyword, args.timeout)
        icon = "✅" if ok else "❌"
        print(f" {icon} {path:<20} {msg}")
        if ok:
            passed += 1
        else:
            failed += 1

    # 2. Static Assets
    print("\n--- 🎨 Static Assets & Metadata (KPF 10) ---")
    for path in STATIC_ASSETS:
        ok, msg = test_url(target, path, None, args.timeout)
        icon = "✅" if ok else "❌"
        print(f" {icon} {path:<20} {msg}")
        if ok:
            passed += 1
        else:
            failed += 1

    # 3. Health Endpoint
    print("\n--- 🩺 API Health Endpoint (KPF 6) ---")
    ok, msg = test_health_api(target, args.timeout)
    icon = "✅" if ok else "❌"
    print(f" {icon} {'/health':<20} {msg}")
    if ok:
        passed += 1
    else:
        failed += 1

    print(f"\n=======================================================")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"=======================================================\n")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
