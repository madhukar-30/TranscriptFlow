"""
config.py — All environment variables and constants.
Loads from .env file if present, otherwise reads from shell environment.
"""

import os
import sys

# ── load .env file if present ─────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional — env vars from shell work fine too

# ── required credentials ──────────────────────────────────────────────────────
NOTION_TOKEN       = os.environ.get("NOTION_TOKEN", "")
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY", "")

# ── notion config ─────────────────────────────────────────────────────────────
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "")

# ── groq model ────────────────────────────────────────────────────────────────
GROQ_MODEL = "llama-3.3-70b-versatile"   # free, fast, high quality

# ── transcript processing ─────────────────────────────────────────────────────
MAX_TRANSCRIPT_CHARS = 40_000   # above this → chunk before summarising
CHUNK_SIZE           = 35_000   # size of each chunk (200-word overlap)

# ── whisper model ─────────────────────────────────────────────────────────────
# Options: "tiny" | "base" | "small" | "medium" | "large-v2"
# tiny/base  — fast, lower accuracy
# small      — good balance (recommended for most machines)
# medium     — high accuracy, slower
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")

# ── browser for yt-dlp cookie auth ───────────────────────────────────────────
# Options: "chrome" | "firefox" | "safari" | "edge"
BROWSER = os.environ.get("BROWSER", "chrome")

# ── valid categories & topics ─────────────────────────────────────────────────
VALID_CATEGORIES = {
    "System Design", "AI / ML", "Networking",
    "Cloud / AWS", "Java", "Python", "DevOps",
}

VALID_TOPICS = {
    "Databases", "Architecture", "Performance", "Protocols",
    "ML / AI", "Caching", "Containers", "OOP", "Concurrency",
    "Collections", "JVM", "Spring", "Design Patterns", "Java",
}

DEFAULT_CATEGORY = "System Design"


def validate():
    """Check required env vars are set. Exit with helpful message if not."""
    errors = []
    if not NOTION_TOKEN:
        errors.append(
            "NOTION_TOKEN not set.\n"
            "  → notion.so/profile/integrations → create integration → copy token"
        )
    if not GROQ_API_KEY:
        errors.append(
            "GROQ_API_KEY not set.\n"
            "  → console.groq.com → API Keys → Create → copy key"
        )
    if not NOTION_DATABASE_ID:
        errors.append(
            "NOTION_DATABASE_ID not set.\n"
            "  → Open your Notion database → copy the ID from the URL"
        )
    if errors:
        print("❌ Missing configuration:\n")
        for e in errors:
            print(f"  • {e}\n")
        print("Set these in a .env file or export them in your shell.")
        sys.exit(1)
