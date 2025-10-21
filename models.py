# models.py
from typing import Dict, Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column, JSON
import hashlib
from collections import Counter

def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def analyze_string(value: str) -> Dict:
    length = len(value)
    # Case-insensitive palindrome check (does not strip spaces unless user wants)
    lowered = value.lower()
    is_palindrome = lowered == lowered[::-1]
    unique_characters = len(set(value))
    # words by whitespace
    word_count = 0 if value.strip() == "" else len(value.split())
    sha = sha256_hex(value)
    freq_map = dict(Counter(value))
    return {
        "length": length,
        "is_palindrome": is_palindrome,
        "unique_characters": unique_characters,
        "word_count": word_count,
        "sha256_hash": sha,
        "character_frequency_map": freq_map,
    }

class StringItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sha256_hash: str = Field(index=True, nullable=False)
    value: str = Field(sa_column=Column("value", Column().type.compiler if False else None))  # fallback; overridden by SQLModel typing
    # store properties as JSON
    properties: Dict = Field(sa_column=Column(JSON), nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

