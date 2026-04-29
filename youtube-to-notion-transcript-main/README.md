# yt-to-notion

Transcribe a YouTube lecture and save structured study notes to your Notion Engineering Notes database — fully free, no paid APIs required.

## Features

- **4-layer transcript fallback** — works on any video:
  1. `youtube-transcript-api` (public video, English captions)
  2. Any available language via `youtube-transcript-api`
  3. `yt-dlp` with browser cookies (members-only / captions disabled in API)
  4. `yt-dlp` audio + local Whisper transcription (transcripts permanently OFF)
- **Free AI summarization** via [Groq](https://console.groq.com) (`llama-3.3-70b-versatile`, 14k requests/day free)
- **Structured Notion pages** with Overview, Key Concepts, Technical Deep Dive, Code Examples, Key Terms, Common Mistakes
- Handles long transcripts with 200-word overlap chunking
- Bypasses Notion's 100-block API limit automatically

## Setup

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/yt-to-notion.git
cd yt-to-notion
pip install -e .
```

### 2. Get free API keys

| Key | Where to get it |
|-----|----------------|
| `NOTION_TOKEN` | [notion.so/profile/integrations](https://notion.so/profile/integrations) → create integration → copy token |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) → API Keys → Create → copy |
| `NOTION_DATABASE_ID` | Open your Notion database → copy the 32-char ID from the URL |

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your values
```

Or export directly in your shell:

```bash
export NOTION_TOKEN="secret_..."
export GROQ_API_KEY="gsk_..."
export NOTION_DATABASE_ID="..."
```

### 4. (Optional) Whisper for offline transcription

Only needed if a video has no captions at all:

```bash
pip install faster-whisper
# Also requires ffmpeg — brew install ffmpeg
```

## Usage

```bash
yt-to-notion <youtube_url> [category]
```

**Category options:** `System Design` | `AI / ML` | `Networking` | `Cloud / AWS` | `Java` | `Python` | `DevOps`

**Examples:**

```bash
# Public video — auto category (System Design)
yt-to-notion "https://www.youtube.com/watch?v=VIDEO_ID"

# Members-only Java video
yt-to-notion "https://www.youtube.com/watch?v=VIDEO_ID" "Java"

# AI lecture
yt-to-notion "https://www.youtube.com/watch?v=VIDEO_ID" "AI / ML"
```

## Configuration

All settings can be set via `.env` or shell environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NOTION_TOKEN` | — | **Required.** Notion integration token |
| `GROQ_API_KEY` | — | **Required.** Groq API key |
| `NOTION_DATABASE_ID` | — | **Required.** Notion database ID |
| `BROWSER` | `chrome` | Browser for yt-dlp cookie auth (`chrome`, `firefox`, `safari`, `edge`) |
| `WHISPER_MODEL` | `base` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large-v2`) |

## How it works

```
YouTube URL
    │
    ▼
extract_video_id()
    │
    ▼
get_transcript()  ──► Attempt 1: youtube-transcript-api (English)
    │                 Attempt 2: youtube-transcript-api (any language)
    │                 Attempt 3: yt-dlp + browser cookies (.vtt subtitles)
    │                 Attempt 4: yt-dlp audio + Whisper transcription
    ▼
summarize()  ──► Groq llama-3.3-70b-versatile
    │            Chunks long transcripts with 200-word overlap
    ▼
save_to_notion()  ──► Creates page in Engineering Notes database
                      Batches blocks in groups of 100 (API limit bypass)
```

## Project structure

```
yt-to-notion/
├── yt_to_notion/
│   ├── __init__.py
│   ├── cli.py           # Entry point — argument parsing, orchestration
│   ├── config.py        # All env vars, constants, validation
│   ├── transcript.py    # 4-attempt transcript fetching
│   ├── summariser.py    # Groq summarization + response parsing
│   └── notion_writer.py # Notion page creation + block conversion
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```
