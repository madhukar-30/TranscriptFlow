"""
summariser.py — Summarize transcript text with Groq (free AI).

Uses llama-3.3-70b-versatile via the Groq API.
Handles long transcripts by chunking with 200-word overlap.
"""

import re

from groq import Groq

from . import config
from .transcript import chunk_text


def summarize(transcript: str, video_url: str, category: str) -> dict:
    """
    Summarize a transcript using Groq.

    Handles long transcripts by splitting into chunks, summarizing each,
    then combining into one final structured summary.

    Returns a dict with keys:
        title, difficulty, topics, key_takeaway,
        overview, key_concepts, technical_deep_dive,
        practical_takeaways, code_examples, key_terms,
        common_mistakes, raw
    """
    client = Groq(api_key=config.GROQ_API_KEY)

    if len(transcript) > config.MAX_TRANSCRIPT_CHARS:
        print(f"  Transcript is long ({len(transcript):,} chars) — summarizing in chunks...")
        chunks = chunk_text(transcript, config.CHUNK_SIZE)
        chunk_summaries = []
        for i, chunk in enumerate(chunks, 1):
            print(f"  Chunk {i}/{len(chunks)}...")
            resp = client.chat.completions.create(
                model=config.GROQ_MODEL,
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": (
                        "Summarize this portion of a lecture transcript into clear, concise bullet points "
                        f"capturing all important technical concepts. Be thorough.\n\n{chunk}"
                    ),
                }],
            )
            chunk_summaries.append(resp.choices[0].message.content)
        combined = "\n\n---\n\n".join(chunk_summaries)
        source_label = "combined chunk summaries"
    else:
        combined = transcript
        source_label = "transcript"

    print(f"  Generating structured summary with Groq ({config.GROQ_MODEL})...")
    prompt = f"""You are a senior software engineer creating DETAILED study notes from a lecture for a fellow developer.
This is a LONG lecture — produce comprehensive, thorough notes. Do NOT be brief.
IMPORTANT: The transcript may be in any language. Always write your entire response in ENGLISH regardless of the transcript language. Translate all concepts to English.

Category context: {category}
Source: {video_url}

Below is the lecture {source_label}. Produce a DETAILED structured technical summary in this EXACT format:

TITLE: <concise descriptive title for the lecture>

DIFFICULTY: <one of: Beginner | Intermediate | Advanced>

TOPICS: <comma-separated from: Databases, Architecture, Performance, Protocols, ML / AI, Caching, Containers, OOP, Concurrency, Collections, JVM, Spring, Design Patterns, Java>

KEY_TAKEAWAY: <single sentence — the most important thing to remember>

OVERVIEW:
<4–6 sentences explaining everything this lecture covers and why each part matters>

KEY_CONCEPTS:
- <concept name>: <thorough 2-3 line explanation of what it is, how it works, and when to use it>
- <cover EVERY major concept from the video — aim for 10-15 bullet points minimum>

TECHNICAL_DEEP_DIVE:
<6–10 paragraphs. Cover each major topic from the lecture in depth. Include:
- How it works internally
- Code patterns or examples if mentioned
- Common pitfalls and mistakes
- Comparison with alternatives
- Real-world usage>

PRACTICAL_TAKEAWAYS:
- <specific actionable point — include code snippets or rules of thumb where relevant>
- <aim for 10+ points>

CODE_EXAMPLES:
<include any important code patterns, snippets, or pseudocode discussed in the lecture>

KEY_TERMS:
- <term>: <clear, complete definition — 2-3 sentences>
- <cover every technical term introduced — aim for 10+ terms>

COMMON_MISTAKES:
- <mistake a developer would make related to this topic>: <how to avoid or fix it>
- <aim for 5+ mistakes>

---
LECTURE {source_label.upper()}:
{combined[:38000]}
"""

    resp = client.chat.completions.create(
        model=config.GROQ_MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.choices[0].message.content
    return parse_summary(raw)


def parse_summary(raw: str) -> dict:
    """Parse the structured Groq output into a dict."""

    def extract(key: str) -> str:
        pattern = rf"^{key}:\s*(.+?)(?=\n[A-Z_]+:|\Z)"
        m = re.search(pattern, raw, re.MULTILINE | re.DOTALL)
        return m.group(1).strip() if m else ""

    def extract_block(key: str) -> str:
        pattern = rf"^{key}:\n(.*?)(?=\n[A-Z_]+:|\Z)"
        m = re.search(pattern, raw, re.MULTILINE | re.DOTALL)
        return m.group(1).strip() if m else ""

    topics_raw = extract("TOPICS")
    topics = [t.strip() for t in topics_raw.split(",") if t.strip() in config.VALID_TOPICS]

    return {
        "title":               extract("TITLE") or "Lecture Summary",
        "difficulty":          extract("DIFFICULTY") or "Intermediate",
        "topics":              topics or ["Architecture"],
        "key_takeaway":        extract("KEY_TAKEAWAY"),
        "overview":            extract_block("OVERVIEW"),
        "key_concepts":        extract_block("KEY_CONCEPTS"),
        "technical_deep_dive": extract_block("TECHNICAL_DEEP_DIVE"),
        "practical_takeaways": extract_block("PRACTICAL_TAKEAWAYS"),
        "code_examples":       extract_block("CODE_EXAMPLES"),
        "key_terms":           extract_block("KEY_TERMS"),
        "common_mistakes":     extract_block("COMMON_MISTAKES"),
        "raw":                 raw,
    }
