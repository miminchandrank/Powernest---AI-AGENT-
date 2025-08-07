# PowerNest AI Agent Platform

![GitHub last commit](https://img.shields.io/github/last-commit/mininchandrank/Powernest---AI-AGENT-)
![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)

FastAPI-powered AI agents for document processing, scheduling, and email automation.

## Features

- **RAG Agent**: Document Q&A from uploaded PDFs
- **Scheduler Agent**: Natural language meeting scheduling
- **Email Agent**: Tone-aware email drafting
- **Profile Agent**: Dynamic user onboarding

## Project Structure
Powernest---AI-AGENT-/
├── app/
│ ├── agents/ # AI agent modules
│ │ ├── rag_agent.py (Document processing)
│ │ ├── scheduler_agent.py (Meeting parsing)
│ │ └── email_agent.py (Email generation)
│ └── main.py (FastAPI entry point)
├── data/ # Storage for user data
├── requirements.txt (Dependencies)
└── .gitignore

text

## Quick Start

### Prerequisites
- Python 3.10+
- Git

### Installation
```bash
git clone https://github.com/mininchandrank/Powernest---AI-AGENT-.git
cd Powernest---AI-AGENT-
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\activate   # Windows
pip install -r requirements.txt
Environment Setup
Create .env file:

ini
OPENROUTER_API_KEY=your_key_here
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
Running the API
bash
uvicorn app.main:app --reload
Access docs at: http://localhost:8000/docs

API Endpoints
Agent	Endpoint	Example Usage
RAG	POST /rag/upload	Upload PDF for Q&A
Scheduler	POST /schedule/parse	"Meet John tomorrow at 2 PM"
Email	POST /email/draft	Generate professional emails
Dependencies
Key packages (see requirements.txt):

fastapi: Web framework

langchain: AI workflows

sentence-transformers: Embeddings

spacy: NLP parsing

Contributing
Fork the repository

Create your feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some AmazingFeature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request

License
MIT

text

Key changes made:
1. Updated all repository references to `mininchandrank/Powernest---AI-AGENT-`
2. Corrected the requirements.txt package names based on your image:
   - `fastapi` (was "fastopi")
   - `openai` (was "opensl")
   - `beautifulsoup4` (was "bountifulsoupd")
3. Maintained the exact repository name with triple hyphens

To use this:
1. Create new `README.md` file in your project root
2. Paste this entire content
3. Commit and push:
```bash
git add README.md
git commit -m "Add professional README"
git push origin main
