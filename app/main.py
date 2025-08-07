from dotenv import load_dotenv
load_dotenv()
import os
from .agents import chat_agent
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .agents import (
    rag_agent,
    scheduler_agent,
    email_agent,
    profile_agent
)

load_dotenv()

app = FastAPI(
    title="AI Agent Platform",
    description="Multi-functional AI Agent with RAG, Scheduling, and Email capabilities",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rag_agent.router, prefix="/rag", tags=["RAG"])
app.include_router(scheduler_agent.router, prefix="/schedule", tags=["Scheduling"])
app.include_router(email_agent.router, prefix="/email", tags=["Email"])
app.include_router(profile_agent.router, prefix="/profile", tags=["Profiling"])
app.include_router(chat_agent.router, prefix="/chat", tags=["Chatbot"])

@app.get("/")
async def root():
    return {"message": "AI Agent Platform - Operational"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)