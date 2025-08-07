from datetime import datetime, timedelta
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Tuple
import spacy
import dateparser
from dateparser.search import search_dates
import re

router = APIRouter()

# Load English NLP model with improved entity recognition
nlp = spacy.load("en_core_web_sm")


class ParseRequest(BaseModel):
    command: str


class ParseResponse(BaseModel):
    person: Optional[str]
    datetime: Optional[str]
    parsed_command: str
    success: bool
    error: Optional[str] = None


def preprocess_text(text: str) -> str:
    """Normalize text for better parsing"""
    replacements = {
        r'\bnoon\b': '12:00 PM',
        r'\bmidnight\b': '00:00',
        r'\bmorning\b': '9:00 AM',
        r'\bevening\b': '6:00 PM',
        r'\btomorrow\b': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    }
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text


def is_valid_name(text: str) -> bool:
    """Check if text is likely a person name"""
    if not text or len(text) < 2:
        return False
    # Common false positives to exclude
    false_positives = {"meeting", "appointment", "schedule", "call", "book"}
    if text.lower() in false_positives:
        return False
    # Should contain at least one alphabetic character and be title case
    return any(c.isalpha() for c in text) and text.istitle()


def extract_person(doc) -> Optional[str]:
    """Advanced name extraction using multiple NLP techniques"""
    # Method 1: Direct name after 'with' preposition
    for token in doc:
        if token.text.lower() == "with" and token.dep_ == "prep":
            for child in token.children:
                if child.dep_ == "pobj" and is_valid_name(child.text):
                    return child.text

    # Method 2: Named Entity Recognition
    for ent in doc.ents:
        if ent.label_ == "PERSON" and is_valid_name(ent.text):
            return ent.text

    # Method 3: Direct object of scheduling verbs
    for token in doc:
        if token.dep_ in ("dobj", "pobj") and token.head.lemma_ in ["meet", "schedule", "book", "call"]:
            if is_valid_name(token.text):
                return token.text

    # Method 4: Pattern matching after trigger words
    trigger_match = re.search(
        r'(?:with|meet|for|schedule|book)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        doc.text,
        re.IGNORECASE
    )
    if trigger_match and is_valid_name(trigger_match.group(1)):
        return trigger_match.group(1)

    return None


def extract_datetime(text: str) -> Optional[datetime]:
    """Robust datetime parsing with context awareness"""
    try:
        dates = search_dates(
            text,
            languages=['en'],
            settings={
                'PREFER_DAY_OF_MONTH': 'first',
                'RELATIVE_BASE': datetime.now(),
                'RETURN_AS_TIMEZONE_AWARE': True,
                'PREFER_LOCALE_DATE_ORDER': False
            }
        )
        return dates[0][1] if dates else None
    except Exception:
        return None


@router.post("/parse", response_model=ParseResponse)
async def parse_appointment(request: ParseRequest):
    command = preprocess_text(request.command.strip())
    try:
        doc = nlp(command)
        person = extract_person(doc)
        dt = extract_datetime(command)

        # Final validation to ensure we didn't capture a verb as name
        if person and any(word in person.lower() for word in ["meet", "schedule", "book"]):
            person = None

        return ParseResponse(
            person=person,
            datetime=dt.isoformat() if dt else None,
            parsed_command=command,
            success=bool(dt)
        )
    except Exception as e:
        return ParseResponse(
            success=False,
            error=f"Parsing failed: {str(e)}",
            parsed_command=command
        )