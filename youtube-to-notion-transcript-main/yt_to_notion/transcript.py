"""
transcript.py — Fetch transcript from a YouTube video.

4-attempt fallback chain:
  1. youtube-transcript-api  → public video, captions ON
  2. Any language variant     → non-English captions
  3. yt-dlp + browser cookies → members-only / captions disabled
  4. yt-dlp audio + Whisper   → transcripts permanently OFF
"""

import os
import re
import sys
import glob
import subprocess
import tempfile

from youtube_transcript_api import YouTubeTranscriptApi

from . import config


def extract_video_id(url: str) -> str:
    """Extract 11-char video ID from any YouTube URL format."""
    patterns = [
        r"(?:v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    sys.exit(f"❌ Could not parse YouTube video ID from: {url}")


def get_transcript(video_id: str) -> tuple[str, str]:
    """
    Returns (transcript_text, language_code).

    Tries 4 methods in order, stopping at first success:
      1. youtube-transcript-api (English)
      2. youtube-transcript-api (any language)
      3. yt-dlp subtitle download (Chrome cookies)
      4. yt-dlp audio + Whisper transcription
    """
    api = YouTubeTranscriptApi()

    # ── Attempt 1: English captions via youtube-transcript-api ───────────────
    try:
        fetched = api.fetch(video_id)
        text = " ".join(s.text for s in fetched)
        return text, "en"
    except Exception:
        pass

    # ── Attempt 2: Any available language ────────────────────────────────────
    try:
        transcript_list = api.list(video_id)
        transcript = next(iter(transcript_list))
        fetched = transcript.fetch()
        text = " ".join(s.text for s in fetched)
        return text, transcript.language_code
    except Exception:
        pass

    # ── Attempt 3: yt-dlp subtitle download (members-only / captions off) ────
    print("  youtube-transcript-api failed → trying yt-dlp with browser cookies...")
    try:
        return _get_transcript_ytdlp(video_id)
    except RuntimeError as e:
        print(f"  yt-dlp subtitles failed ({e}) → falling back to Whisper...")

    # ── Attempt 4: yt-dlp audio + Whisper (transcripts permanently OFF) ──────
    print("  No subtitles available → downloading audio and transcribing with Whisper...")
    return _get_transcript_whisper(video_id)


# ── private helpers ───────────────────────────────────────────────────────────

def _get_transcript_ytdlp(video_id: str) -> tuple[str, str]:
    """
    Download auto-generated .vtt subtitle file using yt-dlp with browser cookies.
    Works for members-only videos and videos with captions disabled in the API.
    Raises RuntimeError if no .vtt file is produced (triggers Whisper fallback).
    """
    url = f"https://www.youtube.com/watch?v={video_id}"

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "subtitle")

        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--cookies-from-browser", config.BROWSER,
            "--write-auto-sub",
            "--sub-lang", "en",
            "--sub-format", "vtt",
            "--skip-download",
            "--output", output_path,
            "--quiet",
            url,
        ]

        print(f"  Running yt-dlp (browser={config.BROWSER})...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp exited with code {result.returncode}: {result.stderr[:200]}")

        vtt_files = glob.glob(os.path.join(tmpdir, "*.vtt"))
        if not vtt_files:
            raise RuntimeError("no .vtt subtitle file produced")

        vtt_text = open(vtt_files[0]).read()

    text = _clean_vtt(vtt_text)
    print(f"  yt-dlp subtitle transcript: {len(text):,} chars")
    return text, "en"


def _get_transcript_whisper(video_id: str) -> tuple[str, str]:
    """
    Download audio via yt-dlp, transcribe locally with faster-whisper.
    100% free, no API key needed. Requires: pip install faster-whisper + ffmpeg.
    Speed: ~5-10 min per 1hr video on CPU (base model).
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("❌ Missing: pip install faster-whisper\n   Also ensure ffmpeg is installed.")

    url = f"https://www.youtube.com/watch?v={video_id}"

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.mp3")

        # download audio only
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--cookies-from-browser", config.BROWSER,
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--output", audio_path,
            "--quiet",
            url,
        ]

        print("  Downloading audio via yt-dlp...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            sys.exit(
                f"❌ yt-dlp audio download failed:\n{result.stderr}\n\n"
                f"Make sure you are logged into YouTube in {config.BROWSER}."
            )

        audio_files = glob.glob(os.path.join(tmpdir, "audio*"))
        if not audio_files:
            sys.exit("❌ Audio download failed — no audio file found.")

        audio_file = audio_files[0]
        print(f"  Audio ready: {os.path.basename(audio_file)}")
        print(f"  Transcribing with Whisper model='{config.WHISPER_MODEL}' (CPU)...")
        print("  This may take 5-10 min for a 1hr video...")

        model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_file, beam_size=5)

        print(f"  Language detected: {info.language} ({info.language_probability:.0%} confidence)")

        text = " ".join(seg.text.strip() for seg in segments)
        print(f"  Whisper transcript: {len(text):,} chars")
        return text, info.language


def _clean_vtt(vtt: str) -> str:
    """Strip VTT timestamps, HTML tags, and duplicate caption lines → plain text."""
    vtt = re.sub(r"WEBVTT.*?\n\n", "", vtt, flags=re.DOTALL)
    vtt = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3} --> .*", "", vtt)
    vtt = re.sub(r"<[^>]+>", "", vtt)
    vtt = re.sub(r"align:\S+.*", "", vtt)
    lines = [l.strip() for l in vtt.split("\n") if l.strip()]
    deduped = [lines[0]] if lines else []
    for line in lines[1:]:
        if line != deduped[-1]:
            deduped.append(line)
    return " ".join(deduped)


def chunk_text(text: str, chunk_size: int) -> list[str]:
    """
    Split long text into chunks of ~chunk_size chars with 200-word overlap.
    Overlap ensures context isn't lost at chunk boundaries.
    """
    words = text.split()
    chunks, current, length = [], [], 0
    for word in words:
        current.append(word)
        length += len(word) + 1
        if length >= chunk_size:
            chunks.append(" ".join(current))
            current = current[-200:]   # keep last 200 words as overlap
            length = sum(len(w) + 1 for w in current)
    if current:
        chunks.append(" ".join(current))
    return chunks
