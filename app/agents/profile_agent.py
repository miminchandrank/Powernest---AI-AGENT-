import os
import asyncio

import json
import uuid
import pandas as pd
from fastapi import APIRouter, HTTPException
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from tqdm import tqdm
from typing import Dict, List, Set
from datetime import datetime, timedelta
from app.models.embeddings import get_embedding_model
from app.utils.validation import validate_email, validate_phone
from app.utils.storage import load_profiles, save_profile

router = APIRouter()

# Configuration
TOPK_PROFILES = 25
MAX_SUGGEST = 5
FIELD_MAPPING = {
    "Full Name": "name",
    "Email Address": "email",
    "Phone Number": "phone",
    "Startup Name": "startup_name"
}

# Global state (use DB in production)
profile_index = None
all_questions = []
records = []
active_sessions: Dict[str, Dict] = {}  # session_id: {profile, asked_questions, last_active}


@router.on_event("startup")
async def init_profile_agent():
    """Initialize profile agent on startup"""
    global profile_index, all_questions, records

    try:
        df = pd.read_csv(os.getenv("PROFILES_CSV"))
        df.columns = df.columns.map(str).str.strip()
        df = df.rename(columns=FIELD_MAPPING)
        all_questions = list(df.columns)

        # Create records
        for idx, row in df.iterrows():
            answered = {
                col: str(row[col]).strip()
                for col in df.columns
                if pd.notna(row[col]) and str(row[col]).strip() not in {"", "nan"}
            }
            records.append({"id": int(idx), "fields": answered})

        # Build index
        model = get_embedding_model()
        emb_vecs = np.vstack([
            model.encode(" ".join(f"{k}: {v}" for k, v in rec["fields"].items()))
            for rec in tqdm(records)
        ]).astype("float32")

        profile_index = faiss.IndexFlatIP(emb_vecs.shape[1])
        profile_index.add(emb_vecs)

    except Exception as e:
        print(f"Profile agent initialization failed: {str(e)}")
        raise


def get_next_questions(user_profile: dict, exclude: Set[str]) -> List[str]:
    """Get next questions with exclusions"""
    global profile_index, all_questions, records

    if not user_profile:
        return [q for q in all_questions if q not in exclude][:MAX_SUGGEST]

    try:
        qtext = " ".join(f"{k}: {v}" for k, v in user_profile.items())
        model = get_embedding_model()
        qvec = model.encode(qtext, normalize_embeddings=True).astype("float32")

        _, neighbor_ids = profile_index.search(qvec.reshape(1, -1), TOPK_PROFILES)
        question_freq = {}

        for idx in neighbor_ids[0]:
            for q in records[idx]["fields"]:
                if q not in user_profile and q not in exclude:
                    question_freq[q] = question_freq.get(q, 0) + 1

        suggested = [q for q, _ in sorted(question_freq.items(), key=lambda x: -x[1])][:MAX_SUGGEST]
        return suggested if suggested else \
            [q for q in all_questions if q not in exclude][:MAX_SUGGEST]

    except Exception as e:
        print(f"Question suggestion failed: {str(e)}")
        return [q for q in all_questions if q not in exclude][:MAX_SUGGEST]


@router.post("/start")
async def start_profile():
    """Start new profile session"""
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        "profile": {},
        "asked_questions": set(),
        "last_active": datetime.now()
    }
    first_question = get_next_questions({}, set())[0]
    active_sessions[session_id]["asked_questions"].add(first_question)
    return {"session_id": session_id, "question": first_question}


@router.post("/submit")
async def submit_profile_response(session_id: str, question: str, answer: str):
    """Submit profile response with validation"""
    try:
        # Validate session
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        session = active_sessions[session_id]
        session["last_active"] = datetime.now()

        # Validate inputs
        if not answer.strip():
            raise ValueError("Answer cannot be empty")

        if "email" in question.lower() and not validate_email(answer):
            raise ValueError("Invalid email format")
        if "phone" in question.lower() and not validate_phone(answer):
            raise ValueError("Invalid phone format")

        # Update profile state
        session["profile"][question] = answer.strip()
        session["asked_questions"].add(question)
        save_profile(session_id, session["profile"])

        # Get next question
        next_qs = get_next_questions(
            session["profile"],
            session["asked_questions"]
        )

        if not next_qs:
            return {
                "status": "complete",
                "profile": session["profile"],
                "session_id": session_id
            }

        next_question = next_qs[0]
        session["asked_questions"].add(next_question)

        return {
            "status": "continue",
            "next_question": next_question,
            "session_id": session_id,
            "progress": f"{len(session['profile'])}/{len(all_questions)}"
        }

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.on_event("shutdown")
async def cleanup_sessions():
    """Clean up session data on shutdown"""
    # In production, would save sessions to persistent storage
    active_sessions.clear()


# Background task to clean stale sessions
async def session_cleaner():
    while True:
        await asyncio.sleep(3600)  # Run hourly
        stale_time = datetime.now() - timedelta(hours=1)
        to_delete = [
            sid for sid, session in active_sessions.items()
            if session["last_active"] < stale_time
        ]
        for sid in to_delete:
            del active_sessions[sid]


@router.on_event("startup")
async def start_cleaner():
    import asyncio
    asyncio.create_task(session_cleaner())