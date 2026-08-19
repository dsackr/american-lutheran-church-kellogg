import os
import subprocess
import difflib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image
import io
from bot.config import REPO_PATH, GCP_PROJECT, GCP_REGION, CLOUD_RUN_SERVICE

# Whitelisted editable files to prevent tampering with system configs
EDITABLE_EXTENSIONS = {".html", ".css", ".js", ".json", ".xml", ".txt", ".md"}


def list_website_files() -> List[str]:
    """Returns a list of editable website files relative to REPO_PATH."""
    files = []
    for p in REPO_PATH.rglob("*"):
        if p.is_file() and p.suffix.lower() in EDITABLE_EXTENSIONS:
            # Skip hidden files or bot folder
            if "bot" in p.parts or ".git" in p.parts:
                continue
            files.append(str(p.relative_to(REPO_PATH)))
    return sorted(files)


def read_website_file(relative_path: str) -> Optional[str]:
    """Reads and returns the contents of a website file."""
    file_path = REPO_PATH / relative_path
    if not file_path.exists() or not file_path.is_file():
        return None
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {e}"


def apply_file_modification(relative_path: str, new_content: str) -> Tuple[bool, str, str]:
    """
    Applies modification to a file and returns (success, diff_text, error_message).
    """
    file_path = REPO_PATH / relative_path
    if not file_path.exists():
        return False, "", f"File '{relative_path}' does not exist."

    old_content = file_path.read_text(encoding="utf-8")
    if old_content == new_content:
        return True, "No changes detected.", ""

    # Generate unified diff
    diff_lines = list(
        difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{relative_path}",
            tofile=f"b/{relative_path}",
            n=3,
        )
    )
    diff_text = "".join(diff_lines)

    try:
        file_path.write_text(new_content, encoding="utf-8")
        return True, diff_text, ""
    except Exception as e:
        return False, "", f"Failed to write file: {e}"


def save_uploaded_asset(image_bytes: bytes, original_filename: str) -> Tuple[bool, str]:
    """
    Saves an uploaded image attachment to assets/images/ with web optimization.
    """
    try:
        images_dir = REPO_PATH / "assets" / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        clean_name = "".join(c for c in original_filename if c.isalnum() or c in ".-_").lower()
        if not clean_name.endswith((".jpg", ".jpeg", ".png", ".webp")):
            clean_name += ".jpg"

        target_path = images_dir / clean_name

        # Optimize image with PIL
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = img.convert("RGB")
            # Resize if overly large (e.g. > 1920px wide)
            if img.width > 1920:
                ratio = 1920 / img.width
                img = img.resize((1920, int(img.height * ratio)), Image.Resampling.LANCZOS)
            img.save(target_path, "JPEG", quality=85, optimize=True)

        return True, f"assets/images/{clean_name}"
    except Exception as e:
        return False, str(e)


def deploy_cloud_run() -> Tuple[bool, str]:
    """
    Triggers Google Cloud Run deployment for the updated site.
    """
    cmd = [
        "gcloud", "run", "deploy", CLOUD_RUN_SERVICE,
        "--source", str(REPO_PATH),
        "--platform", "managed",
        "--region", GCP_REGION,
        "--allow-unauthenticated",
        "--project", GCP_PROJECT,
        "--quiet"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if res.returncode == 0:
            return True, "Cloud Run deployment successful! Site is updated live at https://americanlutheranchurchkellogg.com"
        else:
            return False, f"Deployment failed:\n{res.stderr or res.stdout}"
    except Exception as e:
        return False, f"Deployment error: {e}"
