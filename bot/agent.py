import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
from bot.config import HERMES_API_KEY, HERMES_BASE_URL, HERMES_MODEL
from bot.tools import list_website_files, read_website_file

SYSTEM_PROMPT = """You are the AI Webmaster Agent for American Lutheran Church in Kellogg, Idaho.
Pastor: Pastor Craig Shorey (Email: Cdshorey@gmail.com)
Address: 15 E Mullan Ave, Kellogg, ID 83837
Domains: americanlutheranchurchkellogg.com, alckellogg.com
Phone: (208) 786-7791
Worship Style: Traditional Lutheran Liturgy & Classic Hymnody ONLY (no contemporary/praise band worship).

Your job is to assist church staff and Pastor Craig in making requested changes to the church's static website.
You have tools to view available pages, read page content, and propose clean, accurate updates.

Guidelines:
1. Preserve the website's clean typography, accessibility, and structure.
2. Worship is strictly traditional Lutheran liturgy and hymns (never suggest or add contemporary/praise band elements).
3. All visitor forms route to Pastor Craig at Cdshorey@gmail.com.
4. When asked to update a notice, sermon title, event time, or text, read the relevant file first.
5. Keep changes precise and focused. Do not rewrite unaffected sections.
6. Always explain your proposed changes clearly so church staff can review them before publishing.
"""

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lists all available website files that can be edited (e.g. index.html, about.html, sermons.html, etc.)",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the current content of a specific website file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Relative path to file, e.g. 'index.html', 'about.html', 'css/styles.css'",
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
            "description": "Proposes an updated complete content for a file after making the requested modifications.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Relative path to the file to modify",
                    },
                    "summary_of_changes": {
                        "type": "string",
                        "description": "A clear, 1-2 sentence human summary of what was modified.",
                    },
                    "updated_content": {
                        "type": "string",
                        "description": "The complete updated file content with the edits applied.",
                    },
                },
                "required": ["filename", "summary_of_changes", "updated_content"],
            },
        },
    },
]


class HermesWebmasterAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=HERMES_API_KEY or "dummy_key",
            base_url=HERMES_BASE_URL,
        )

    def process_request(self, user_prompt: str, image_asset_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes an agent loop to interpret the user's change request, read necessary files,
        and propose the exact edit.
        """
        prompt = user_prompt
        if image_asset_path:
            prompt += f"\n[User attached an image saved at: {image_asset_path}]"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        # Multi-turn tool execution loop
        for _ in range(6):
            response = self.client.chat.completions.create(
                model=HERMES_MODEL,
                messages=messages,
                tools=TOOLS_SPEC,
                tool_choice="auto",
                temperature=0.2,
            )

            msg = response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                return {
                    "type": "reply",
                    "text": msg.content or "I have processed your message.",
                }

            # Execute tool calls
            for tool in msg.tool_calls:
                fn_name = tool.function.name
                args = json.loads(tool.function.arguments)

                if fn_name == "list_files":
                    files = list_website_files()
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "content": json.dumps({"files": files}),
                    })

                elif fn_name == "read_file":
                    fname = args.get("filename", "")
                    content = read_website_file(fname)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "content": json.dumps({"filename": fname, "content": content}),
                    })

                elif fn_name == "propose_file_edit":
                    return {
                        "type": "proposal",
                        "filename": args["filename"],
                        "summary": args["summary_of_changes"],
                        "updated_content": args["updated_content"],
                    }

        return {
            "type": "reply",
            "text": "Completed reviewing request.",
        }
