import os
import logging
from typing import List, Dict
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
from app.utils.storage import save_email_draft
from datetime import datetime

load_dotenv()

# Configuration
LLM_MODEL = "anthropic/claude-3-haiku"  # Unified model
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

router = APIRouter()
logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)


class EmailRequest(BaseModel):
    recipient: str
    subject: str
    tone: Optional[str] = "professional"
    details: Optional[str] = ""


def build_email_prompt(request: EmailRequest) -> List[Dict]:
    """Optimized prompt for Claude-3-Haiku email drafting"""
    return [
        {
            "role": "system",
            "content": f"""You are an expert email assistant. Draft a {request.tone} email with:

            Requirements:
            1. Strictly follow this structure:
               - Greeting: "Dear [Name],"
               - Body: 2-3 concise paragraphs
               - Closing: "Best regards,"
               - Signature: "[Your Name]"
            2. Tone: {request.tone}
            3. Never use placeholders like [Your Name] - omit if unknown"""
        },
        {
            "role": "user",
            "content": f"""Recipient: {request.recipient}
            Subject: {request.subject}
            Key Details: {request.details}"""
        }
    ]


@router.post("/draft")
async def draft_email(request: EmailRequest = Body(...)):
    if not OPENROUTER_API_KEY:
        raise HTTPException(503, "API key missing")

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=build_email_prompt(request),
            max_tokens=500,
            temperature=0.7,
            top_p=0.9
        )

        draft = response.choices[0].message.content.strip()

        # Post-processing validation
        if not draft or len(draft.split()) < 20:
            raise ValueError("Incomplete draft generated")

        try:
            save_email_draft(request.recipient, request.subject, draft)
        except Exception as e:
            logger.warning(f"Draft not saved: {str(e)}")

        return {
            "draft": draft,
            "model": LLM_MODEL,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Email generation failed: {str(e)}")
        raise HTTPException(500, f"Email drafting failed: {str(e)}")