"""
notion_writer.py — Build Notion page content and save to Engineering Notes database.

Handles the Notion API 100-block limit by appending blocks in batches.
"""

import re
import textwrap
from datetime import date

from notion_client import Client as NotionClient

from . import config


def build_notion_content(summary: dict, video_url: str, transcript_len: int) -> str:
    """Assemble the full Notion page body as a markdown-like string."""
    sections = []

    sections.append(
        f'<callout icon="🎥" color="blue_bg">\n'
        f'**Source:** [{video_url}]({video_url})\n'
        f'**Transcript length:** {transcript_len:,} characters\n'
        f'</callout>'
    )
    sections.append(f"## 📋 Overview\n\n{summary['overview']}")
    sections.append(f"## 💡 Key Concepts\n\n{summary['key_concepts']}")
    sections.append(f"## 🔬 Technical Deep Dive\n\n{summary['technical_deep_dive']}")
    sections.append(f"## ✅ Practical Takeaways\n\n{summary['practical_takeaways']}")
    if summary.get("code_examples"):
        sections.append(f"## 💻 Code Examples\n\n{summary['code_examples']}")
    sections.append(f"## 📖 Key Terms\n\n{summary['key_terms']}")
    if summary.get("common_mistakes"):
        sections.append(f"## ⚠️ Common Mistakes\n\n{summary['common_mistakes']}")

    return "\n\n---\n\n".join(sections)


def save_to_notion(summary: dict, video_url: str, category: str, content: str) -> str:
    """
    Create a page in the Engineering Notes database.

    Splits blocks into batches of 100 to bypass the Notion API limit.
    Returns the URL of the created page.
    """
    notion = NotionClient(auth=config.NOTION_TOKEN)

    today = date.today().isoformat()
    difficulty = summary["difficulty"] if summary["difficulty"] in ("Beginner", "Intermediate", "Advanced") else "Intermediate"

    all_blocks = notion_blocks_from_markdown(content)
    first_batch  = all_blocks[:100]
    extra_blocks = all_blocks[100:]

    response = notion.pages.create(
        parent={"database_id": config.NOTION_DATABASE_ID},
        icon={"type": "emoji", "emoji": "🎥"},
        properties={
            "Note": {
                "title": [{"text": {"content": summary["title"]}}]
            },
            "Category": {
                "select": {"name": category}
            },
            "Topic": {
                "multi_select": [{"name": t} for t in summary["topics"]]
            },
            "Difficulty": {
                "select": {"name": difficulty}
            },
            "Status": {
                "status": {"name": "In progress"}
            },
            "Key Takeaway": {
                "rich_text": [{"text": {"content": summary["key_takeaway"][:2000]}}]
            },
            "Last Reviewed": {
                "date": {"start": today}
            },
        },
        children=first_batch,
    )
    page_id = response["id"]

    for i in range(0, len(extra_blocks), 100):
        batch = extra_blocks[i:i + 100]
        notion.blocks.children.append(page_id, children=batch)
        print(f"     Appended block batch {i // 100 + 2}...")

    return response["url"]


def notion_blocks_from_markdown(content: str) -> list:
    """Convert a markdown-like string to a list of Notion block objects."""
    blocks = []
    for line in content.split("\n"):
        if line.startswith("## "):
            blocks.append({
                "object": "block", "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:]}}]},
            })
        elif line.startswith("### "):
            blocks.append({
                "object": "block", "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:]}}]},
            })
        elif line.startswith("- "):
            blocks.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]},
            })
        elif line.startswith("---"):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        elif line.startswith("<callout"):
            inner = re.sub(r"<[^>]+>", "", line).strip()
            if not inner and blocks:
                continue
            blocks.append({
                "object": "block", "type": "callout",
                "callout": {
                    "icon": {"type": "emoji", "emoji": "🎥"},
                    "rich_text": [{"type": "text", "text": {"content": inner}}],
                },
            })
        elif line.strip():
            for para in textwrap.wrap(line, 1900) or [line]:
                blocks.append({
                    "object": "block", "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": para}}]},
                })

    return blocks
