# TranscriptFlow

A Python-based tool to transcribe YouTube videos and generate structured study notes, built using **Python**, **YouTube Transcript API**, **Groq API**, and **Notion API**. The application automates transcript extraction, summarization, and storage into Notion for organized learning.

---

## 🚀 Usage
Run the CLI tool to process any YouTube video:

transcriptflow <youtube_url> [category]

---

## ✨ Features
* **Transcript Extraction:** Retrieves transcripts from YouTube using multiple fallback strategies.
* **4-Layer Fallback System:** Handles public, private, and caption-disabled videos using API, yt-dlp, and Whisper.
* **AI Summarization:** Generates structured notes using Groq LLM (`llama-3.3-70b-versatile`).
* **Notion Integration:** Automatically saves notes into a Notion database.
* **Structured Output:** Organizes notes into sections like Overview, Key Concepts, and Technical Details.
* **Chunk Processing:** Handles long transcripts using overlapping chunking for better summarization.
* **Automation:** End-to-end pipeline from video input to organized notes.

---

## 🛠 Tech Stack
| Component | Technology |
| :--- | :--- |
| **Language** | Python |
| **Transcript Extraction** | YouTube Transcript API, yt-dlp |
| **AI Integration** | Groq API (LLM) |
| **Database / Storage** | Notion API |
| **Audio Processing** | Whisper (optional) |

---

## ⚙️ Configuration

The application uses environment variables for secure configuration.

### Environment Variables

* NOTION_TOKEN: Notion integration token  
* GROQ_API_KEY: Groq API key  
* NOTION_DATABASE_ID: Notion database ID  
* BROWSER: Browser for yt-dlp authentication (default: chrome)  
* WHISPER_MODEL: Whisper model size (default: base)  

---

## 💻 Setup

### Clone Repository

git clone https://github.com/madhukar-30/TranscriptFlow.git  
cd TranscriptFlow  

### Install Dependencies

pip install -e .  

### Configure Environment

cp .env.example .env  

Edit the `.env` file with your credentials.

---

## ☁️ How it Works

YouTube URL  
→ Extract video ID  
→ Fetch transcript (multi-step fallback)  
→ Process and chunk text  
→ Generate summary using LLM  
→ Save structured notes to Notion  

---

## 🧠 Key Learnings
* Working with multiple APIs including YouTube, Groq, and Notion.
* Implementing fallback strategies for reliable data extraction.
* Handling large text data through chunking and preprocessing.
* Applying prompt-based techniques for structured summarization.
* Automating workflows using Python scripting.

---

## 👤 Author
**Manas Madhukar**