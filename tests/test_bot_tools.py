import io
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image
import pytest

from bot.tools import (
    EDITABLE_EXTENSIONS,
    list_website_files,
    read_website_file,
    apply_file_modification,
    save_uploaded_asset,
    deploy_cloud_run,
)


def test_editable_extensions_whitelist():
    """Ensures whitelisted extensions cover standard website files and exclude executable binaries/secrets."""
    assert ".html" in EDITABLE_EXTENSIONS
    assert ".css" in EDITABLE_EXTENSIONS
    assert ".js" in EDITABLE_EXTENSIONS
    assert ".json" in EDITABLE_EXTENSIONS
    assert ".md" in EDITABLE_EXTENSIONS
    assert ".py" not in EDITABLE_EXTENSIONS  # Python code shouldn't be edited by bot tools directly
    assert ".env" not in EDITABLE_EXTENSIONS  # Environment files excluded


def test_list_website_files(tmp_path, monkeypatch):
    """Tests file listing excludes bot/ and .git/ directories and only includes allowed extensions."""
    monkeypatch.setattr("bot.tools.REPO_PATH", tmp_path)

    # Create dummy files
    (tmp_path / "index.html").write_text("<h1>Home</h1>", encoding="utf-8")
    (tmp_path / "about.html").write_text("<h1>About</h1>", encoding="utf-8")
    (tmp_path / "css").mkdir()
    (tmp_path / "css" / "styles.css").write_text("body { color: black; }", encoding="utf-8")

    # Files that should be excluded
    (tmp_path / "bot").mkdir()
    (tmp_path / "bot" / "agent.py").write_text("print('bot')", encoding="utf-8")
    (tmp_path / "bot" / "notes.md").write_text("bot notes", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("git config", encoding="utf-8")
    (tmp_path / "unknown.bin").write_bytes(b"\x00\x01\x02")

    files = list_website_files()
    assert "index.html" in files
    assert "about.html" in files
    assert str(Path("css/styles.css")) in files or "css/styles.css" in files
    assert not any(f.startswith("bot") for f in files)
    assert not any(f.startswith(".git") for f in files)
    assert "unknown.bin" not in files


def test_read_website_file_existing(tmp_path, monkeypatch):
    """Tests reading an existing file returns its UTF-8 content."""
    monkeypatch.setattr("bot.tools.REPO_PATH", tmp_path)
    test_file = tmp_path / "sermons.html"
    test_file.write_text("<p>Sermon Title</p>", encoding="utf-8")

    content = read_website_file("sermons.html")
    assert content == "<p>Sermon Title</p>"


def test_read_website_file_nonexistent(tmp_path, monkeypatch):
    """Tests reading a nonexistent file returns None."""
    monkeypatch.setattr("bot.tools.REPO_PATH", tmp_path)
    content = read_website_file("does-not-exist.html")
    assert content is None


def test_apply_file_modification_success(tmp_path, monkeypatch):
    """Tests applying modification produces unified diff and updates the file."""
    monkeypatch.setattr("bot.tools.REPO_PATH", tmp_path)
    target = tmp_path / "index.html"
    target.write_text("Line 1\nLine 2\nLine 3\n", encoding="utf-8")

    new_content = "Line 1\nLine 2 Modified\nLine 3\n"
    success, diff, err = apply_file_modification("index.html", new_content)

    assert success is True
    assert err == ""
    assert "-Line 2" in diff
    assert "+Line 2 Modified" in diff
    assert target.read_text(encoding="utf-8") == new_content


def test_apply_file_modification_no_change(tmp_path, monkeypatch):
    """Tests applying identical content returns no changes."""
    monkeypatch.setattr("bot.tools.REPO_PATH", tmp_path)
    target = tmp_path / "visit.html"
    target.write_text("<p>Sunday at 10 AM</p>", encoding="utf-8")

    success, diff, err = apply_file_modification("visit.html", "<p>Sunday at 10 AM</p>")
    assert success is True
    assert diff == "No changes detected."
    assert err == ""


def test_apply_file_modification_missing_file(tmp_path, monkeypatch):
    """Tests applying modification to a missing file returns an error."""
    monkeypatch.setattr("bot.tools.REPO_PATH", tmp_path)
    success, diff, err = apply_file_modification("ghost.html", "some text")
    assert success is False
    assert "does not exist" in err


def test_save_uploaded_asset_resizing_and_optimization(tmp_path, monkeypatch, sample_image_bytes):
    """Tests image asset saving converts RGBA to RGB JPEG and downscales wide images."""
    monkeypatch.setattr("bot.tools.REPO_PATH", tmp_path)

    success, rel_path = save_uploaded_asset(sample_image_bytes, "hero_banner.jpg")
    assert success is True
    assert rel_path == "assets/images/hero_banner.jpg"

    saved_file = tmp_path / "assets" / "images" / "hero_banner.jpg"
    assert saved_file.exists()

    with Image.open(saved_file) as img:
        assert img.format == "JPEG"
        assert img.mode == "RGB"
        assert img.width == 1920  # Resized down from 2400
        assert img.height == 960   # Maintained 2:1 aspect ratio


def test_save_uploaded_asset_invalid_image(tmp_path, monkeypatch):
    """Tests saving corrupt image bytes returns error."""
    monkeypatch.setattr("bot.tools.REPO_PATH", tmp_path)
    success, err = save_uploaded_asset(b"not-an-image", "test.jpg")
    assert success is False
    assert err != ""


@patch("subprocess.run")
def test_deploy_cloud_run_success(mock_subproc):
    """Tests successful Cloud Run deployment invocation."""
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_subproc.return_value = mock_res

    success, msg = deploy_cloud_run()
    assert success is True
    assert "Cloud Run deployment successful" in msg


@patch("subprocess.run")
def test_deploy_cloud_run_failure(mock_subproc):
    """Tests failed Cloud Run deployment invocation."""
    mock_res = MagicMock()
    mock_res.returncode = 1
    mock_res.stderr = "Error deploying service"
    mock_res.stdout = ""
    mock_subproc.return_value = mock_res

    success, msg = deploy_cloud_run()
    assert success is False
    assert "Deployment failed" in msg
