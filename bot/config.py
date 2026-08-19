import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Discord Configuration
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
AUTHORIZED_USER_IDS = [
    int(uid.strip())
    for uid in os.getenv("AUTHORIZED_USER_IDS", "").split(",")
    if uid.strip().isdigit()
]

# Hermes / LLM Configuration
HERMES_API_KEY = os.getenv("HERMES_API_KEY", os.getenv("OPENAI_API_KEY", ""))
HERMES_BASE_URL = os.getenv("HERMES_BASE_URL", "https://openrouter.ai/api/v1")
HERMES_MODEL = os.getenv("HERMES_MODEL", "nousresearch/hermes-3-llama-3.1-70b")

# Repository & GCP Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_PATH = Path(os.getenv("REPO_PATH", str(BASE_DIR)))
GCP_PROJECT = os.getenv("GCP_PROJECT", "openclaw-gateway-489207")
GCP_REGION = os.getenv("GCP_REGION", "us-west1")
CLOUD_RUN_SERVICE = os.getenv("CLOUD_RUN_SERVICE", "alc-kellogg")
