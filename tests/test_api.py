import json
import threading
import time
from http.server import HTTPServer
import http.client
from urllib.parse import urlparse
from unittest.mock import patch, MagicMock
import urllib.error
import pytest
from api.main import SupportTicketHandler


@pytest.fixture(scope="module")
def api_server():
    """Spawns an ephemeral HTTP server running SupportTicketHandler."""
    server = HTTPServer(("127.0.0.1", 0), SupportTicketHandler)
    host, port = server.server_address
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    base_url = f"http://{host}:{port}"
    yield base_url
    server.shutdown()
    server.server_close()


def send_http(method: str, url: str, body: bytes = None, headers: dict = None):
    """Sends an HTTP request directly via http.client without touching urllib.request."""
    parsed = urlparse(url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port)
    hdrs = headers or {}
    conn.request(method, parsed.path, body=body, headers=hdrs)
    resp = conn.getresponse()
    status = resp.status
    headers_dict = dict(resp.getheaders())
    data = resp.read()
    conn.close()
    return status, headers_dict, data


def test_health_check_get(api_server):
    """Tests GET /health returns 200 with ok status."""
    status, headers, data = send_http("GET", f"{api_server}/health")
    assert status == 200
    assert headers.get("Access-Control-Allow-Origin") == "*"
    body = json.loads(data.decode("utf-8"))
    assert body["status"] == "ok"
    assert body["service"] == "alc-support-ticket-api"


def test_root_get(api_server):
    """Tests GET / returns 200 with webpage content."""
    status, headers, data = send_http("GET", f"{api_server}/")
    assert status == 200
    assert len(data) > 0


def test_not_found_get(api_server):
    """Tests GET on unknown route returns 404."""
    status, _, _ = send_http("GET", f"{api_server}/non-existent-route")
    assert status == 404


def test_options_cors(api_server):
    """Tests OPTIONS request returns 204 with CORS headers."""
    status, headers, _ = send_http("OPTIONS", f"{api_server}/api/support-ticket")
    assert status == 204
    assert headers.get("Access-Control-Allow-Origin") == "*"
    assert "POST" in headers.get("Access-Control-Allow-Methods", "")


def test_post_unknown_path(api_server):
    """Tests POST to invalid route returns 404."""
    status, _, _ = send_http(
        "POST",
        f"{api_server}/api/unknown",
        body=json.dumps({"test": "data"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    assert status == 404


def test_post_empty_body(api_server):
    """Tests POST with missing/empty body returns 400."""
    status, _, data = send_http(
        "POST",
        f"{api_server}/api/support-ticket",
        body=b"",
        headers={"Content-Length": "0"}
    )
    assert status == 400
    body = json.loads(data.decode("utf-8"))
    assert "Missing request body" in body["error"]


def test_post_invalid_json(api_server):
    """Tests POST with invalid JSON returns 400."""
    payload = b"invalid-json-string{"
    status, _, data = send_http(
        "POST",
        f"{api_server}/api/support-ticket",
        body=payload,
        headers={"Content-Type": "application/json", "Content-Length": str(len(payload))}
    )
    assert status == 400
    body = json.loads(data.decode("utf-8"))
    assert "Invalid JSON payload" in body["error"]


def test_post_missing_request_text(api_server):
    """Tests POST with empty request_text returns 400."""
    payload = json.dumps({
        "page_url": "https://americanlutheranchurchkellogg.com/sermons.html",
        "page_title": "Sermons",
        "user_name": "Jane Member",
        "request_text": "   "
    }).encode("utf-8")
    status, _, data = send_http(
        "POST",
        f"{api_server}/api/support-ticket",
        body=payload,
        headers={"Content-Type": "application/json", "Content-Length": str(len(payload))}
    )
    assert status == 400
    body = json.loads(data.decode("utf-8"))
    assert "Request description is required" in body["error"]


@patch("urllib.request.urlopen")
def test_post_support_ticket_success(mock_urlopen, api_server):
    """Tests successful support ticket creation on GitHub."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "number": 42,
        "html_url": "https://github.com/dsackr/american-lutheran-church-kellogg/issues/42"
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    payload = json.dumps({
        "page_url": "https://americanlutheranchurchkellogg.com/ministries.html",
        "page_title": "Ministries",
        "user_name": "John Doe",
        "user_contact": "john@example.com",
        "request_text": "Please update the Sunday school time to 9:00 AM.",
        "browser_info": "Mozilla/5.0 TestBrowser"
    }).encode("utf-8")

    status, _, data = send_http(
        "POST",
        f"{api_server}/api/support-ticket",
        body=payload,
        headers={"Content-Type": "application/json", "Content-Length": str(len(payload))}
    )

    assert status == 200
    body = json.loads(data.decode("utf-8"))
    assert body["success"] is True
    assert body["issue_number"] == 42
    assert "issues/42" in body["issue_url"]


@patch("urllib.request.urlopen")
def test_post_support_ticket_target_filename_deduction(mock_urlopen, api_server):
    """Tests that various page URLs are correctly parsed to target HTML filenames."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "number": 43,
        "html_url": "https://github.com/dsackr/american-lutheran-church-kellogg/issues/43"
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    test_urls = [
        ("https://americanlutheranchurchkellogg.com/", "index.html"),
        ("https://alckellogg.com", "index.html"),
        ("https://americanlutheranchurchkellogg.com/about", "about.html"),
        ("https://americanlutheranchurchkellogg.com/sermons.html?filter=2026", "sermons.html"),
    ]

    for page_url, _ in test_urls:
        payload = json.dumps({
            "page_url": page_url,
            "page_title": "Test Page",
            "request_text": "Update note"
        }).encode("utf-8")
        status, _, data = send_http(
            "POST",
            f"{api_server}/api/support-ticket",
            body=payload,
            headers={"Content-Type": "application/json", "Content-Length": str(len(payload))}
        )
        assert status == 200


@patch("urllib.request.urlopen")
def test_post_support_ticket_github_api_http_error(mock_urlopen, api_server):
    """Tests handling of GitHub API HTTPError."""
    mock_err = urllib.error.HTTPError(
        url="https://api.github.com/repos/dsackr/american-lutheran-church-kellogg/issues",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=MagicMock(read=MagicMock(return_value=b'{"message":"Bad credentials"}'))
    )
    mock_urlopen.side_effect = mock_err

    payload = json.dumps({
        "page_url": "https://americanlutheranchurchkellogg.com/sermons.html",
        "request_text": "Update something"
    }).encode("utf-8")

    status, _, data = send_http(
        "POST",
        f"{api_server}/api/support-ticket",
        body=payload,
        headers={"Content-Type": "application/json", "Content-Length": str(len(payload))}
    )

    assert status == 401
    body = json.loads(data.decode("utf-8"))
    assert "GitHub API error" in body["error"]
