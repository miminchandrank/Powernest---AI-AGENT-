# PowerNest AI Agent Platform



**FastAPI-powered AI agents for document processing, scheduling, and email automation.**

---

## 🚀 Features

- **RAG Agent**: Document Q&A from uploaded PDFs  
- **Scheduler Agent**: Natural language meeting scheduling  
- **Email Agent**: Tone-aware email drafting  
- **Profile Agent**: Dynamic user onboarding  
- **Chat Agent**: General conversational AI  

---

## 📁 Project Structure

Powernest---AI-AGENT-/
├── app/
│ ├── agents/ # AI agent modules
│ │ ├── rag_agent.py # Document processing
│ │ ├── scheduler_agent.py # Meeting parsing
│ │ ├── email_agent.py # Email generation
│ │ └── chat_agent.py # Conversational AI
│ └── main.py # FastAPI entry point
├── data/ # Storage for user data
├── requirements.txt # Dependencies
└── .gitignore


### ✅ Prerequisites

- Python 3.10+
- Git


🔐 Environment Setup
Create a .env file in the project root:

OPENROUTER_API_KEY=your_key_here



▶️ Running the API
uvicorn app.main:app --reload

Visit your API docs at:
👉 http://localhost:8000/docs

📡 API Endpoints
Agent	Endpoint	Method	Description
RAG	/rag/upload	POST	Upload PDF for Q&A
RAG	/rag/query	POST	Query uploaded document
Scheduler	/schedule/parse	POST	Parse natural language meeting requests
Email	/email/draft	POST	Generate tone-aware emails
Chat	/chat/message	POST	General conversational AI
Profile	/profile/start	POST	Initialize user profile session
Profile	/profile/submit	POST	Submit profile responses

