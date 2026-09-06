import os
import sys
from pathlib import Path
import pytest

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def repo_root():
    return REPO_ROOT


@pytest.fixture
def sample_image_bytes():
    """Generates valid PNG image bytes for testing PIL optimization."""
    from PIL import Image
    import io

    # Create a 2400x1200 RGBA image (wider than 1920 to test resizing)
    img = Image.new("RGBA", (2400, 1200), color=(100, 150, 200, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def mock_html_pages(repo_root):
    """Returns a list of all primary website HTML files."""
    pages = [
        "index.html",
        "about.html",
        "visit.html",
        "ministries.html",
        "sermons.html",
        "give.html",
    ]
    return [repo_root / page for page in pages]
