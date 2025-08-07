import re

def validate_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def validate_phone(phone: str) -> bool:
    return bool(re.match(r"^[\d\s+-]{8,}$", phone))