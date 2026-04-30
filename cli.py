"""
cli.py — Command-line entry point for yt-to-notion.

Usage:
   TranscriptFlow <youtube_url> [category]

    category: "System Design" | "AI / ML" | "Networking" | "Cloud / AWS"
              "Java" | "Python" | "DevOps"
              (defaults to "System Design")
"""

import os
import sys

from . import config
from .transcript import extract_video_id, get_transcript
from .summariser import summarize
from .notion_writer import build_notion_content, save_to_notion

# ensure local ffmpeg binary is on PATH if present at ~/ffmpeg
_home = os.path.expanduser("~")
if os.path.isfile(os.path.join(_home, "ffmpeg")):
    os.environ["PATH"] = _home + ":" + os.environ.get("PATH", "")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    config.validate()

    video_url = sys.argv[1]
    category  = sys.argv[2] if len(sys.argv) > 2 else config.DEFAULT_CATEGORY

    if category not in config.VALID_CATEGORIES:
        print(f"Warning: '{category}' is not a recognised category.")
        print(f"Valid options: {', '.join(sorted(config.VALID_CATEGORIES))}")
        print(f"Defaulting to '{config.DEFAULT_CATEGORY}'")
        category = config.DEFAULT_CATEGORY

    print(f"\n🎥  YouTube → Notion")
    print(f"   URL      : {video_url}")
    print(f"   Category : {category}")
    print()

    # 1. transcript
    print("1/3  Fetching transcript...")
    video_id = extract_video_id(video_url)
    transcript, lang = get_transcript(video_id)
    print(f"     Got {len(transcript):,} chars (language: {lang})")

    # 2. summarise
    print("2/3  Summarising with Groq...")
    summary = summarize(transcript, video_url, category)
    print(f"     Title     : {summary['title']}")
    print(f"     Difficulty: {summary['difficulty']}")
    print(f"     Topics    : {', '.join(summary['topics'])}")

    # 3. save to notion
    print("3/3  Saving to Notion Engineering Notes database...")
    content = build_notion_content(summary, video_url, len(transcript))
    notion_url = save_to_notion(summary, video_url, category, content)
    print(f"\n✅  Done! Notion page: {notion_url}\n")


if __name__ == "__main__":
    main()
