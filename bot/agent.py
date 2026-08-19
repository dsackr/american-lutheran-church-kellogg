import json
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI
from bot.config import (
    HERMES_API_KEY,
    HERMES_BASE_URL,
    HERMES_MODEL,
    BOT_NAME,
    CHURCH_NAME,
    CHURCH_LOCATION,
    PASTOR_NAME,
    PASTOR_EMAIL,
    PRIMARY_DOMAIN,
    GITHUB_USERNAME,
)
from bot.github_client import ALCGitHubClient

logger = logging.getLogger("ALC_Support.Agent")

SYSTEM_PROMPT = f"""You are '{BOT_NAME}', the autonomous AI Webmaster & Technical Assistant for {CHURCH_NAME} in Kellogg, Idaho.
Church Details:
- Location: {CHURCH_LOCATION}
- Pastor: {PASTOR_NAME}
- Pastor Email: {PASTOR_EMAIL}
- Website: {PRIMARY_DOMAIN}
- GitHub Committer Account: {GITHUB_USERNAME}
- Worship Style: STRICTLY Traditional Lutheran Liturgy, Historic Hymnody, and Faithful Scripture Preaching (No contemporary or praise band worship).

Your primary role is to assist church staff and Pastor Craig with making accurate, respectful, and well-formatted updates to the church's static website.
You inspect repository files on GitHub, interpret user requests, and generate clean, unified changes.

Guidelines:
1. Always maintain high aesthetic standards, clean semantic HTML5, modern CSS tokens, and web accessibility.
2. Worship is strictly traditional Lutheran (never add contemporary/praise band wording).
3. All visitor forms route directly to Pastor Craig at {PASTOR_EMAIL}.
4. Read the relevant files first before proposing changes.
5. Provide a clear, polite explanation of what you are proposing to change so the pastor can review and approve with one click.
"""

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lists all editable website files currently in the GitHub repository (e.g. index.html, about.html, sermons.html, css/styles.css, etc.).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the latest content of a specific file from the GitHub repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Path to file, e.g. 'index.html', 'about.html', 'sermons.html', 'js/main.js'",
                    }
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_file_edit",
            "description": "Proposes the complete updated file content with the requested changes applied.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Relative path to the file being updated.",
                    },
                    "summary_of_changes": {
                        "type": "string",
                        "description": "A clear, 1-2 sentence summary of what was updated.",
                    },
                    "commit_message": {
                        "type": "string",
                        "description": "A concise Git commit message (e.g. 'update Thanksgiving service announcement')",
                    },
                    "updated_content": {
                        "type": "string",
                        "description": "The complete new content for the file.",
                    },
                },
                "required": ["filename", "summary_of_changes", "commit_message", "updated_content"],
            },
        },
    },
]


class ALCSupportHermesAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=HERMES_API_KEY or "dummy_key",
            base_url=HERMES_BASE_URL,
        )
        self.github = ALCGitHubClient()

    def process_request(self, user_prompt: str, image_asset_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Processes a user request through the Hermes agent function-calling loop.
        """
        prompt = user_prompt
        if image_asset_path:
            prompt += f"\n[User uploaded image asset at: {image_asset_path}]"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        for _ in range(6):
            try:
                response = self.client.chat.completions.create(
                    model=HERMES_MODEL,
                    messages=messages,
                    tools=TOOLS_SPEC,
                    tool_choice="auto",
                    temperature=0.2,
                )
            except Exception as e:
                logger.error(f"Hermes API error: {e}")
                return {
                    "type": "reply",
                    "text": f"⚠️ Encountered an error communicating with Hermes model: {e}",
                }

            msg = response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                return {
                    "type": "reply",
                    "text": msg.content or "I have reviewed your request.",
                }

            for tool in msg.tool_calls:
                fn_name = tool.function.name
                args = json.loads(tool.function.arguments)

                if fn_name == "list_files":
                    files = self.github.list_files()
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "content": json.dumps({"files": files}),
                    })

                elif fn_name == "read_file":
                    fname = args.get("filename", "")
                    content = self.github.read_file(fname)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "content": json.dumps({"filename": fname, "content": content or "File not found."}),
                    })

                elif fn_name == "propose_file_edit":
                    return {
                        "type": "proposal",
                        "filename": args["filename"],
                        "summary": args["summary_of_changes"],
                        "commit_message": args.get("commit_message", "update website content"),
                        "updated_content": args["updated_content"],
                    }

        return {
            "type": "reply",
            "text": "Completed processing request.",
        }
