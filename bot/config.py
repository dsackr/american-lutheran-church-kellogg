import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Agent Identity
BOT_NAME = "ALC Support"
CHURCH_NAME = "American Lutheran Church"
CHURCH_LOCATION = "15 E Mullan Ave, Kellogg, ID 83837"
PASTOR_NAME = "Pastor Craig Shorey"
PASTOR_EMAIL = "Cdshorey@gmail.com"
PRIMARY_DOMAIN = "https://americanlutheranchurchkellogg.com"

# Discord Configuration
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
AUTHORIZED_USER_IDS = [
    int(uid.strip())
    for uid in os.getenv("AUTHORIZED_USER_IDS", "").split(",")
    if uid.strip().isdigit()
]

# GitHub Integration (alckellogg Account)
GITHUB_PAT = os.getenv("GITHUB_PAT", "")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "alckellogg")
GITHUB_REPO = os.getenv("GITHUB_REPO", "dsackr/american-lutheran-church-kellogg")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

# Hermes / LLM Configuration
HERMES_API_KEY = os.getenv("HERMES_API_KEY", os.getenv("OPENAI_API_KEY", ""))
HERMES_BASE_URL = os.getenv("HERMES_BASE_URL", "https://openrouter.ai/api/v1")
HERMES_MODEL = os.getenv("HERMES_MODEL", "nousresearch/hermes-3-llama-3.1-70b")

# Local Workspace (if running alongside local clone)
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_PATH = Path(os.getenv("REPO_PATH", str(BASE_DIR)))
