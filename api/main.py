import os
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.getenv("GITHUB_REPO", "dsackr/american-lutheran-church-kellogg").strip()
PORT = int(os.getenv("PORT", "8080"))

ALLOWED_ORIGINS = [
    "https://americanlutheranchurchkellogg.com",
    "https://www.americanlutheranchurchkellogg.com",
    "https://alckellogg.com",
    "https://www.alckellogg.com",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]


class SupportTicketHandler(BaseHTTPRequestHandler):
    def _set_cors(self):
        origin = self.headers.get("Origin", "*")
        if origin in ALLOWED_ORIGINS or "*" in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
        else:
            self.send_header("Access-Control-Allow-Origin", "https://americanlutheranchurchkellogg.com")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "alc-support-ticket-api"}).encode("utf-8"))
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path != "/api/support-ticket" and self.path != "/":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._send_json(400, {"error": "Missing request body"})
            return

        try:
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)
        except Exception as e:
            self._send_json(400, {"error": f"Invalid JSON payload: {str(e)}"})
            return

        page_url = data.get("page_url", "Unknown page")
        page_title = data.get("page_title", "Website Page")
        user_name = data.get("user_name", "Anonymous Contributor")
        user_contact = data.get("user_contact", "Not provided")
        request_text = data.get("request_text", "").strip()
        browser_info = data.get("browser_info", "Not provided")

        if not request_text:
            self._send_json(400, {"error": "Request description is required."})
            return

        # Determine target file name from URL path
        path_clean = page_url.split("?")[0].split("#")[0].strip("/")
        filename = path_clean.split("/")[-1] if path_clean else "index.html"
        if not filename or filename == "americanlutheranchurchkellogg.com" or filename == "alckellogg.com":
            filename = "index.html"
        if not filename.endswith(".html") and not "." in filename:
            filename += ".html"

        # Create title
        summary_title = request_text.split("\n")[0][:60]
        issue_title = f"[Website Support] {filename}: {summary_title}"

        # Markdown body
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        issue_body = f"""### 🎫 Website Support Ticket

**Page Name:** `{page_title}`
**Target URL:** {page_url}
**Target File:** `{filename}`
**Submitted By:** {user_name} ({user_contact})
**Timestamp:** {timestamp}
**Client Info:** {browser_info}

---

### 📝 Requested Change / Issue Description:
```text
{request_text}
```

---
*Created automatically via the ALC Kellogg Website Support Widget.*
"""

        # Call GitHub API
        github_url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
        payload = {
            "title": issue_title,
            "body": issue_body,
        }

        req = urllib.request.Request(
            github_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "ALC-Support-Widget",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                issue_number = res_data.get("number")
                issue_html_url = res_data.get("html_url")

                self._send_json(200, {
                    "success": True,
                    "issue_number": issue_number,
                    "issue_url": issue_html_url,
                    "message": "Support ticket created successfully on GitHub."
                })
        except urllib.error.HTTPError as he:
            err_msg = he.read().decode("utf-8")
            self._send_json(he.code, {"error": f"GitHub API error: {err_msg}"})
        except Exception as e:
            self._send_json(500, {"error": f"Internal server error: {str(e)}"})

    def _send_json(self, status_code: int, data: dict):
        self.send_response(status_code)
        self._set_cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


def run():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, SupportTicketHandler)
    print(f"ALC Support Ticket API server running on port {PORT}...")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
