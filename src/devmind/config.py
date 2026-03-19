"""
Config — loads environment variables and defines project-wide constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Required ───────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]
GITHUB_TOKEN: str = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]

# ── Filesystem MCP root ────────────────────────────────────────────────────────
# The MCP filesystem server sandboxes access to this directory.
# Default: user's home directory.
FS_ROOT_PATH: str = os.getenv("FS_ROOT_PATH", str(Path.home()))

# ── Session / Memory ───────────────────────────────────────────────────────────
SESSION_ID: str = os.getenv("SESSION_ID", "devmind-user")
DB_PATH: str = os.getenv("DB_PATH", "data/conversations.db")

# ── Models ─────────────────────────────────────────────────────────────────────
TRIAGE_MODEL: str = os.getenv("TRIAGE_MODEL", "gpt-4o-mini")
SPECIALIST_MODEL: str = os.getenv("SPECIALIST_MODEL", "gpt-4o")

# ── Output guardrail ───────────────────────────────────────────────────────────
MAX_RESPONSE_CHARS: int = 2000  # cap for text responses

# ── Ensure DB directory exists ─────────────────────────────────────────────────
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
