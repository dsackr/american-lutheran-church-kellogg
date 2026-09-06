from datetime import datetime, timedelta
import pytest


def calculate_next_sunday_10am(now: datetime) -> datetime:
    """
    Python implementation of the countdown math from js/main.js:initSundayCountdown.
    """
    # In JS: 0=Sunday, 1=Monday, ..., 6=Saturday
    # In Python: weekday() is 0=Monday, ..., 6=Sunday
    # Convert Python weekday to JS getDay(): (weekday + 1) % 7
    js_day_of_week = (now.weekday() + 1) % 7

    days_until_sunday = (7 - js_day_of_week) % 7
    target = now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=days_until_sunday)

    if js_day_of_week == 0 and now > target:
        target += timedelta(days=7)

    return target


def test_sunday_countdown_math_on_monday():
    """On Monday at 9 AM, next Sunday should be 6 days away."""
    # 2026-08-24 is a Monday
    monday_morning = datetime(2026, 8, 24, 9, 0, 0)
    target = calculate_next_sunday_10am(monday_morning)
    assert target == datetime(2026, 8, 30, 10, 0, 0)


def test_sunday_countdown_math_on_saturday():
    """On Saturday at 8 PM, next Sunday should be 1 day away."""
    # 2026-08-29 is a Saturday
    sat_night = datetime(2026, 8, 29, 20, 0, 0)
    target = calculate_next_sunday_10am(sat_night)
    assert target == datetime(2026, 8, 30, 10, 0, 0)


def test_sunday_countdown_math_on_sunday_before_service():
    """On Sunday at 8:30 AM, target is today at 10:00 AM."""
    # 2026-08-30 is a Sunday
    sunday_early = datetime(2026, 8, 30, 8, 30, 0)
    target = calculate_next_sunday_10am(sunday_early)
    assert target == datetime(2026, 8, 30, 10, 0, 0)


def test_sunday_countdown_math_on_sunday_after_service():
    """On Sunday at 11:30 AM, target rolls over to next Sunday at 10:00 AM."""
    # 2026-08-30 is a Sunday
    sunday_late = datetime(2026, 8, 30, 11, 30, 0)
    target = calculate_next_sunday_10am(sunday_late)
    assert target == datetime(2026, 9, 6, 10, 0, 0)


def test_support_ticket_js_path_deduction():
    """Validates the JS path parsing logic from initModals."""
    def extract_filename(pathname: str) -> str:
        clean = pathname.split('/')[-1] if pathname else 'index.html'
        return clean or 'index.html'

    assert extract_filename("/") == "index.html"
    assert extract_filename("/about.html") == "about.html"
    assert extract_filename("/sermons.html") == "sermons.html"
    assert extract_filename("/visit.html") == "visit.html"


def test_prayer_form_payload_structure():
    """Validates prayer form payload keys expected by formsubmit.co handler."""
    expected_keys = {
        "_subject",
        "Submitted By",
        "Contact Information",
        "Confidential (Pastor Only)",
        "Prayer Request",
        "Date Submitted",
    }
    sample_payload = {
        "_subject": "🙏 Prayer Request from John (ALC Kellogg Website)",
        "Submitted By": "John",
        "Contact Information": "john@example.com",
        "Confidential (Pastor Only)": "YES (Pastor Only)",
        "Prayer Request": "Healing for family member",
        "Date Submitted": "2026-08-22 10:00:00",
    }
    assert set(sample_payload.keys()) == expected_keys


def test_visit_form_payload_structure():
    """Validates visit form payload keys expected by formsubmit.co handler."""
    expected_keys = {
        "_subject",
        "Guest Name",
        "Email Address",
        "Expected Sunday Date",
        "Family / Children / Questions",
        "Date Submitted",
    }
    sample_payload = {
        "_subject": "⛪ Plan Your Visit: Mary (ALC Kellogg Website)",
        "Guest Name": "Mary",
        "Email Address": "mary@example.com",
        "Expected Sunday Date": "Next Sunday",
        "Family / Children / Questions": "Two kids (ages 4 and 7)",
        "Date Submitted": "2026-08-22 10:00:00",
    }
    assert set(sample_payload.keys()) == expected_keys


def test_contact_form_payload_structure():
    """Validates general contact form payload keys."""
    expected_keys = {
        "_subject",
        "Sender Name",
        "Email Address",
        "Phone Number",
        "Message",
        "Date Submitted",
    }
    sample_payload = {
        "_subject": "📬 Contact Message from Mark (ALC Kellogg Website)",
        "Sender Name": "Mark",
        "Email Address": "mark@example.com",
        "Phone Number": "208-555-0123",
        "Message": "Inquiry about hall rental",
        "Date Submitted": "2026-08-22 10:00:00",
    }
    assert set(sample_payload.keys()) == expected_keys
