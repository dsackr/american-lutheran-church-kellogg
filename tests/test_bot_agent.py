import json
from unittest.mock import patch, MagicMock
import pytest

from bot.agent import SYSTEM_PROMPT, TOOLS_SPEC, ALCSupportHermesAgent
from bot.github_client import ALCGitHubClient


def test_system_prompt_critical_boundaries():
    """Validates the system prompt strictly contains theology, contact, and security boundaries."""
    assert "American Lutheran Church" in SYSTEM_PROMPT
    assert "15 E Mullan Ave, Kellogg, ID 83837" in SYSTEM_PROMPT
    assert "Pastor Craig Shorey" in SYSTEM_PROMPT
    assert "Cdshorey@gmail.com" in SYSTEM_PROMPT
    assert "Traditional Lutheran Liturgy" in SYSTEM_PROMPT
    assert "dsackr/american-lutheran-church-kellogg" in SYSTEM_PROMPT
    assert "alckellogg" in SYSTEM_PROMPT


def test_tools_spec_schema():
    """Validates tools spec contains list_files, read_file, and propose_file_edit functions."""
    tool_names = [t["function"]["name"] for t in TOOLS_SPEC]
    assert "list_files" in tool_names
    assert "read_file" in tool_names
    assert "propose_file_edit" in tool_names

    # Check propose_file_edit schema
    propose_tool = next(t for t in TOOLS_SPEC if t["function"]["name"] == "propose_file_edit")
    params = propose_tool["function"]["parameters"]["properties"]
    assert "filename" in params
    assert "summary_of_changes" in params
    assert "commit_message" in params
    assert "updated_content" in params


@patch("bot.agent.OpenAI")
def test_agent_process_request_text_reply(mock_openai_cls):
    """Tests agent returning a direct text response."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client

    mock_choice = MagicMock()
    mock_choice.message.tool_calls = None
    mock_choice.message.content = "I can help with that."
    mock_response = MagicMock(choices=[mock_choice])
    mock_client.chat.completions.create.return_value = mock_response

    agent = ALCSupportHermesAgent()
    result = agent.process_request("Hello, what is the church address?")

    assert result["type"] == "reply"
    assert "I can help with that." in result["text"]


@patch("bot.agent.OpenAI")
def test_agent_process_request_propose_file_edit(mock_openai_cls):
    """Tests agent returning a propose_file_edit tool call."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client

    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "propose_file_edit"
    mock_tool_call.function.arguments = json.dumps({
        "filename": "index.html",
        "summary_of_changes": "Update service time notice",
        "commit_message": "feat(website): update service notice",
        "updated_content": "<html><body>New Content</body></html>"
    })

    mock_choice = MagicMock()
    mock_choice.message.tool_calls = [mock_tool_call]
    mock_response = MagicMock(choices=[mock_choice])
    mock_client.chat.completions.create.return_value = mock_response

    agent = ALCSupportHermesAgent()
    result = agent.process_request("Change the service notice on the home page")

    assert result["type"] == "proposal"
    assert result["filename"] == "index.html"
    assert result["summary"] == "Update service time notice"
    assert result["commit_message"] == "feat(website): update service notice"
    assert "New Content" in result["updated_content"]


@patch("bot.agent.OpenAI")
def test_agent_process_request_error_handling(mock_openai_cls):
    """Tests agent handling LLM API exceptions gracefully."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("OpenRouter connection failed")

    agent = ALCSupportHermesAgent()
    result = agent.process_request("Update sermon title")

    assert result["type"] == "reply"
    assert "⚠️ Encountered an error" in result["text"]


@patch("bot.github_client.Github")
def test_github_client_list_files(mock_github_cls):
    """Tests ALCGitHubClient.list_files filtering."""
    mock_gh = MagicMock()
    mock_github_cls.return_value = mock_gh
    mock_repo = MagicMock()
    mock_gh.get_repo.return_value = mock_repo

    elem1 = MagicMock(type="blob", path="index.html")
    elem2 = MagicMock(type="blob", path="bot/config.py")  # Should be excluded
    elem3 = MagicMock(type="blob", path="css/styles.css")
    elem4 = MagicMock(type="blob", path=".github/workflows/deploy.yml")  # Should be excluded

    mock_tree = MagicMock(tree=[elem1, elem2, elem3, elem4])
    mock_repo.get_git_tree.return_value = mock_tree

    client = ALCGitHubClient()
    files = client.list_files()

    assert "index.html" in files
    assert "css/styles.css" in files
    assert "bot/config.py" not in files
    assert ".github/workflows/deploy.yml" not in files


@patch("bot.github_client.Github")
def test_github_client_read_file(mock_github_cls):
    """Tests ALCGitHubClient.read_file decodes content."""
    mock_gh = MagicMock()
    mock_github_cls.return_value = mock_gh
    mock_repo = MagicMock()
    mock_gh.get_repo.return_value = mock_repo

    mock_content = MagicMock()
    mock_content.decoded_content = b"<!DOCTYPE html><html><body>ALC</body></html>"
    mock_repo.get_contents.return_value = mock_content

    client = ALCGitHubClient()
    content = client.read_file("index.html")

    assert "<!DOCTYPE html>" in content
    assert "ALC" in content


@patch("bot.github_client.Github")
def test_github_client_commit_file_change(mock_github_cls):
    """Tests ALCGitHubClient.commit_file_change updates file."""
    mock_gh = MagicMock()
    mock_github_cls.return_value = mock_gh
    mock_repo = MagicMock()
    mock_gh.get_repo.return_value = mock_repo

    mock_content = MagicMock(sha="abc123sha")
    mock_repo.get_contents.return_value = mock_content
    mock_commit = MagicMock(html_url="https://github.com/dsackr/american-lutheran-church-kellogg/commit/abc123sha")
    mock_repo.update_file.return_value = {"commit": mock_commit}

    client = ALCGitHubClient()
    success, msg, url = client.commit_file_change("about.html", "<h1>About Updated</h1>", "update pastor bio")

    assert success is True
    assert "Successfully committed" in msg
    assert "commit/abc123sha" in url


@patch("bot.github_client.Github")
def test_github_client_get_latest_workflow_run(mock_github_cls):
    """Tests ALCGitHubClient.get_latest_workflow_run returns latest CI run."""
    mock_gh = MagicMock()
    mock_github_cls.return_value = mock_gh
    mock_repo = MagicMock()
    mock_gh.get_repo.return_value = mock_repo

    mock_run = MagicMock(
        id=987654,
        name="Deploy to Google Cloud Run",
        status="completed",
        conclusion="success",
        html_url="https://github.com/dsackr/american-lutheran-church-kellogg/actions/runs/987654",
        head_commit=MagicMock(message="feat: update sermon schedule")
    )
    mock_runs = MagicMock(totalCount=1)
    mock_runs.__getitem__.return_value = mock_run
    mock_repo.get_workflow_runs.return_value = mock_runs

    client = ALCGitHubClient()
    info = client.get_latest_workflow_run()

    assert info is not None
    assert info["id"] == 987654
    assert info["status"] == "completed"
    assert info["conclusion"] == "success"
