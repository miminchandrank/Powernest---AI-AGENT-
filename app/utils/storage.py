import os
import json
import pandas as pd
from icalendar import Calendar
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def _ensure_directory_exists(path: str):
    """Helper function to ensure directory exists"""
    os.makedirs(path, exist_ok=True)

def _safe_json_load(filepath: str, default: Any = None):
    """Safely load JSON file with error handling"""
    try:
        with open(filepath, 'r') as f:
            # Check if file is empty
            content = f.read().strip()
            if not content:
                return default if default is not None else []
            return json.loads(content)
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON in {filepath}, resetting file")
        return default if default is not None else []
    except FileNotFoundError:
        return default if default is not None else []
    except Exception as e:
        logger.error(f"Error reading {filepath}: {str(e)}")
        return default if default is not None else []

# Profile storage
def save_profile(session_id: str, profile: dict):
    try:
        path = "data/profiles"
        _ensure_directory_exists(path)
        with open(f"{path}/{session_id}.json", "w") as f:
            json.dump(profile, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save profile: {str(e)}")
        raise

def save_conversation(session_id: str, history: list):
    try:
        path = "data/conversations"
        _ensure_directory_exists(path)
        with open(f"{path}/{session_id}.json", "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save conversation: {str(e)}")
        raise

def load_profiles() -> Dict[str, Any]:
    profiles = {}
    path = "data/profiles"
    try:
        _ensure_directory_exists(path)
        for file in os.listdir(path):
            if file.endswith(".json"):
                file_path = os.path.join(path, file)
                profile_data = _safe_json_load(file_path, {})
                if profile_data:  # Only add if we got valid data
                    profiles[file.split(".")[0]] = profile_data
    except Exception as e:
        logger.error(f"Error loading profiles: {str(e)}")
    return profiles

# Calendar storage
def save_calendar(cal: Calendar):
    try:
        _ensure_directory_exists("data")
        with open("data/calendar.ics", "wb") as f:
            f.write(cal.to_ical())
    except Exception as e:
        logger.error(f"Failed to save calendar: {str(e)}")
        raise

def load_calendar() -> Calendar:
    try:
        _ensure_directory_exists("data")
        if os.path.exists("data/calendar.ics"):
            with open("data/calendar.ics", "rb") as f:
                return Calendar.from_ical(f.read())
    except Exception as e:
        logger.error(f"Error loading calendar: {str(e)}")
    return Calendar()

# Email storage
def save_email_draft(recipient: str, subject: str, content: str):
    try:
        _ensure_directory_exists("data")
        drafts = load_email_drafts()
        drafts.append({
            "recipient": recipient,
            "subject": subject,
            "content": content,
            "timestamp": pd.Timestamp.now().isoformat()
        })
        with open("data/emails.json", "w") as f:
            json.dump(drafts, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save email draft: {str(e)}")
        raise

def load_email_drafts() -> List[Dict[str, str]]:
    return _safe_json_load("data/emails.json", [])