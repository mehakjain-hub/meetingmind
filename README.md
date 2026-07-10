# MeetingMind
 
**AI meeting assistant: audio → transcript → speaker diarization → structured minutes (summary, decisions, action items) via LLM. Deployed with Postgres.**
 
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL-336791.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
 
---
 
## Overview
 
MeetingMind is an end-to-end system that takes raw meeting audio and turns it into structured Minutes of Meeting — a summary, key decisions, assigned action items with deadlines, and an agenda-completion check — all served through a deployed, usable web app.
 
Everything runs on a self-hosted pipeline (no third-party ASR API offload): audio goes in, structured, speaker-attributed minutes come out.
 
## Pipeline
 
```
Audio upload (Streamlit)
  → FFmpeg preprocessing
  → Whisper transcription (faster-whisper, int8 quantized)
  → pyannote speaker diarization
  → whisperX forced alignment (merge transcript + speaker segments)
  → transcript cleaner
  → LLM structured extraction (Pydantic schemas)
  → PostgreSQL (via SQLAlchemy)
  → Streamlit results view + export
```
 
## Features
 
- **Transcription** — `faster-whisper` (int8 quantized) for fast, accurate speech-to-text with word-level timestamps
- **Speaker diarization** — `pyannote.audio` identifies who said what
- **Alignment** — `whisperX` forced phoneme-level alignment fixes timestamp drift between Whisper and pyannote before merging
- **Structured extraction** — LLM-based summary, decisions, and action items (assignee/task/deadline), validated against Pydantic schemas
- **Agenda tracking** — compares transcript/summary against a supplied agenda and reports covered vs. not-covered items
- **Persistent storage** — PostgreSQL schema for meetings, transcripts, summaries, and action items
- **Web app** — Streamlit interface for upload, results view, and meeting history
- **Export** — download results as Markdown/PDF
  
## Tech Stack
 
| Layer | Tools |
|---|---|
| Audio preprocessing | FFmpeg |
| Transcription | faster-whisper (int8 quantized) |
| Alignment | whisperX |
| Diarization | pyannote.audio |
| Structured extraction | LLM API (Claude/GPT/Qwen) + Pydantic |
| Database | PostgreSQL + SQLAlchemy |
| Frontend | Streamlit |
| Export | Markdown / fpdf2 or reportlab |
| Deployment | HuggingFace Spaces |
| Hosted DB | Supabase / Neon |
 
## Repository Structure
 
```
meetingmind/
├── app/
│   ├── pipeline/
│   │   ├── preprocess.py       # FFmpeg audio preprocessing
│   │   ├── transcribe.py       # Whisper transcription
│   │   ├── diarize.py          # pyannote speaker diarization
│   │   ├── merge.py            # merge transcript + speaker segments
│   │   ├── clean.py            # transcript cleaner
│   │   └── extract.py          # LLM structured extraction
│   ├── db/
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── session.py          # DB engine/session setup
│   │   └── crud.py             # insert/fetch functions
│   ├── schemas/
│   │   └── extraction.py       # Pydantic schemas
│   └── frontend/
│       ├── streamlit_app.py
│       ├── pages/
│       │   ├── upload.py
│       │   ├── results.py
│       │   └── history.py
│       └── utils/
│           └── export.py
├── tests/
├── sample_data/
├── docs/
│   ├── architecture.png
│   └── screenshots/
├── .env.example
├── requirements.txt
├── docker-compose.yml
└── README.md
```
 
## Setup
 
### Prerequisites
- Python 3.10+
- FFmpeg installed and on your `PATH`
- PostgreSQL (local install, or a hosted instance for deployment)
- HuggingFace account + access token (for pyannote gated models)
- An LLM API key (Claude/GPT/Qwen)
  
### Installation
 
```bash
# clone the repo
git clone https://github.com/mehakjain-hub/meetingmind.git
cd meetingmind
 
# create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
 
# install dependencies
pip install -r requirements.txt
 
# configure environment variables
cp .env .env
# edit .env with your DB connection string, HF token, and LLM API key
```
 
### Database setup
 
```bash
createdb meetingmind
```
 
Schema is created automatically via SQLAlchemy on first run (or run migrations if provided).
 
### Running locally
 
```bash
streamlit run app/frontend/streamlit_app.py
```
 
Then open the local URL Streamlit prints (typically `http://localhost:8501`), upload a meeting recording, and let the pipeline run.
 
## Usage
 
1. Upload an audio file (meeting recording) through the web app.
2. The pipeline preprocesses, transcribes, diarizes, and cleans the audio automatically.
3. Structured minutes are generated: summary, decisions, action items, and agenda status.
4. Review results in the app, or export as Markdown/PDF.
5. Past meetings are browsable from the history page.
   
## Known Limitations
 
- **Input length capped at ~15 minutes** on the deployed version to stay within free-tier CPU/RAM limits. Longer meetings are rejected with a clear message rather than timing out or crashing.
- Deployed version uses smaller/quantized Whisper and pyannote models to run on constrained hardware; the local/dev setup can use larger models for higher accuracy.
- Diarization accuracy can degrade with overlapping speech or poor audio quality.

## Evaluation
 
Pipeline was evaluated on a set of 8–10 sample meetings, with manual review of diarization accuracy and action-item extraction quality. *(See `docs/` for detailed findings.)*
 
## Roadmap / Stretch Goals
 
- Docker containerization for the full app
- GitHub Actions CI
- pytest coverage
- Follow-up email generation
- Multilingual support
- Real-time meeting support
## License
 
MIT — see [LICENSE](LICENSE) for details.
