"""
Simple rule-based handlers for greetings and farewells.
"""
import re

def is_greeting(text: str) -> bool:
    patterns = [r"\bhi\b", r"\bhello\b", r"how are you", r"good day"]
    return any(re.search(pat, text, re.IGNORECASE) for pat in patterns)


def is_farewell(text: str) -> bool:
    patterns = [r"\bbye\b", r"see you", r"goodbye"]
    return any(re.search(pat, text, re.IGNORECASE) for pat in patterns)
