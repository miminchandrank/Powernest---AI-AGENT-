import os
from fastapi import APIRouter, HTTPException
from openai import OpenAI
from typing import Dict
from datetime import datetime, timedelta
import uuid
import asyncio
from app.utils.storage import save_conversation

router = APIRouter()

# Initialize client (OpenRouter or direct OpenAI)
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"  # Remove this line for direct OpenAI
)

# Session storage
active_sessions: Dict[str, dict] = {}

SYSTEM_PROMPT = """You are StartupPal, a friendly AI assistant for our investment platform. 

Guidelines:
- Answer questions about the platform
- Be concise (1-2 sentences)
- Admit when you don't know something
- Never offer to schedule meetings or analyze documents"""


@router.post("/start")
async def start_session():
    """Initialize new chat session"""
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        "history": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": "How can I help you today?"}
        ],
        "created_at": datetime.now()
    }
    return {"session_id": session_id}


@router.post("/message")
async def handle_message(session_id: str, message: str):
    """Handle general chat messages only"""
    if session_id not in active_sessions:
        raise HTTPException(404, "Session not found")

    # Add user message to history
    active_sessions[session_id]["history"].append(
        {"role": "user", "content": message}
    )

    try:
        # Generate response
        response = client.chat.completions.create(
            model="anthropic/claude-3-haiku",  # Or any other model
            messages=active_sessions[session_id]["history"],
            max_tokens=300,
            temperature=0.7
        )

        ai_response = response.choices[0].message.content

        # Update history
        active_sessions[session_id]["history"].append(
            {"role": "assistant", "content": ai_response}
        )

        return {"response": ai_response}

    except Exception as e:
        raise HTTPException(500, f"Chat failed: {str(e)}")


# Session cleanup (same as before)
async def clean_sessions():
    while True:
        await asyncio.sleep(3600)
        stale_time = datetime.now() - timedelta(hours=2)
        stale_sessions = [
            sid for sid, data in active_sessions.items()
            if data["created_at"] < stale_time
        ]
        for sid in stale_sessions:
            del active_sessions[sid]


@router.on_event("startup")
async def startup_tasks():
    asyncio.create_task(clean_sessions())


@router.on_event("shutdown")
async def save_conversations():
    for sid, data in active_sessions.items():
        save_conversation(sid, data["history"])