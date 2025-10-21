# main.py
from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel, Session, create_engine, select
from typing import Optional, List, Dict, Any
from models import StringItem, analyze_string, sha256_hex
from pydantic import BaseModel
from datetime import datetime, timezone
import re

# --- Config ---
DATABASE_URL = "sqlite:///./strings.db"
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

app = FastAPI(title="String Analyzer Service - Stage 1")

# create tables
def init_db():
    SQLModel.metadata.create_all(engine)

@app.on_event("startup")
def on_startup():
    init_db()

# --- Pydantic schemas for requests/responses ---
class CreateStringRequest(BaseModel):
    value: str

class PropertiesSchema(BaseModel):
    length: int
    is_palindrome: bool
    unique_characters: int
    word_count: int
    sha256_hash: str
    character_frequency_map: Dict[str, int]

class StringResponse(BaseModel):
    id: str
    value: str
    properties: PropertiesSchema
    created_at: datetime

# --- Helper functions ---
def find_by_sha(session: Session, sha: str) -> Optional[StringItem]:
    statement = select(StringItem).where(StringItem.sha256_hash == sha)
    result = session.exec(statement).first()
    return result

def find_by_value(session: Session, value: str) -> Optional[StringItem]:
    sha = sha256_hex(value)
    return find_by_sha(session, sha)

# --- Endpoints ---

@app.post("/strings", response_model=StringResponse, status_code=201)
def create_string(payload: CreateStringRequest = Body(...)):
    if payload is None or "value" not in payload.dict():
        raise HTTPException(status_code=400, detail='Invalid request body or missing "value" field')
    if not isinstance(payload.value, str):
        raise HTTPException(status_code=422, detail='"value" must be a string')

    props = analyze_string(payload.value)
    sha = props["sha256_hash"]

    with Session(engine) as session:
        existing = find_by_sha(session, sha)
        if existing:
            # conflict
            raise HTTPException(
                status_code=409,
                detail="String already exists in the system"
            )
        item = StringItem(sha256_hash=sha, value=payload.value, properties=props)
        session.add(item)
        session.commit()
        session.refresh(item)

    resp = {
        "id": sha,
        "value": payload.value,
        "properties": props,
        "created_at": item.created_at,
    }
    return JSONResponse(status_code=201, content=resp)

@app.get("/strings/{string_value}", response_model=StringResponse)
def get_string(string_value: str = Path(..., description="URL-encoded string value to look up")):
    # expect caller to URL encode the string_value
    with Session(engine) as session:
        item = find_by_value(session, string_value)
        if not item:
            raise HTTPException(status_code=404, detail="String does not exist in the system")
        resp = {
            "id": item.sha256_hash,
            "value": item.value,
            "properties": item.properties,
            "created_at": item.created_at,
        }
        return resp

@app.get("/strings")
def list_strings(
    is_palindrome: Optional[bool] = Query(None),
    min_length: Optional[int] = Query(None, ge=0),
    max_length: Optional[int] = Query(None, ge=0),
    word_count: Optional[int] = Query(None, ge=0),
    contains_character: Optional[str] = Query(None, min_length=1, max_length=1),
):
    # validate query combinations
    if min_length is not None and max_length is not None and min_length > max_length:
        raise HTTPException(status_code=400, detail="min_length cannot be greater than max_length")

    with Session(engine) as session:
        statement = select(StringItem)
        results = session.exec(statement).all()

    filtered: List[Dict[str, Any]] = []
    for item in results:
        p = item.properties
        ok = True
        if is_palindrome is not None and p.get("is_palindrome") != is_palindrome:
            ok = False
        if min_length is not None and p.get("length", 0) < min_length:
            ok = False
        if max_length is not None and p.get("length", 0) > max_length:
            ok = False
        if word_count is not None and p.get("word_count") != word_count:
            ok = False
        if contains_character is not None and contains_character not in item.value:
            ok = False
        if ok:
            filtered.append({
                "id": item.sha256_hash,
                "value": item.value,
                "properties": p,
                "created_at": item.created_at,
            })

    resp = {
        "data": filtered,
        "count": len(filtered),
        "filters_applied": {
            k: v for k, v in {
                "is_palindrome": is_palindrome,
                "min_length": min_length,
                "max_length": max_length,
                "word_count": word_count,
                "contains_character": contains_character,
            }.items() if v is not None
        }
    }
    return resp

# Natural language filtering heuristics
def parse_nl_query(query: str) -> Dict:
    # returns parsed_filters or raise ValueError
    q = query.lower().strip()
    parsed = {}

    # simple numeric capture: "longer than X characters" → min_length = X+1 as spec example
    m = re.search(r"longer than\s+(\d+)\s+characters?", q)
    if m:
        num = int(m.group(1))
        parsed["min_length"] = num + 1

    m = re.search(r"shorter than\s+(\d+)\s+characters?", q)
    if m:
        num = int(m.group(1))
        parsed["max_length"] = num - 1 if num > 0 else 0

    # "strings longer than 10 characters" was given in examples -> handled above.

    if "palindrom" in q or "palindrome" in q:
        parsed["is_palindrome"] = True

    if "single word" in q or "one word" in q:
        parsed["word_count"] = 1

    # "contain the first vowel" heuristic -> 'a'
    if "first vowel" in q:
        parsed["contains_character"] = "a"

    # "strings containing the letter z" or "contain the letter z"
    m = re.search(r"letter\s+([a-z])", q)
    if m:
        parsed["contains_character"] = m.group(1)

    # "containing the letter z" or "contain z"
    m2 = re.search(r"contain(?:ing)?\s+([a-z])", q)
    if m2:
        parsed["contains_character"] = m2.group(1)

    # If nothing parsed, raise
    if not parsed:
        raise ValueError("Unable to parse natural language query")

    # Basic conflict detection: e.g., min_length > max_length
    if "min_length" in parsed and "max_length" in parsed:
        if parsed["min_length"] > parsed["max_length"]:
            raise ValueError("Parsed filters conflict: min_length > max_length")

    return parsed

@app.get("/strings/filter-by-natural-language")
def filter_by_nl(query: str = Query(..., min_length=1)):
    try:
        parsed = parse_nl_query(query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # reuse list_strings logic by applying parsed filters
    try:
        # Validate types etc.
        response = list_strings(
            is_palindrome=parsed.get("is_palindrome"),
            min_length=parsed.get("min_length"),
            max_length=parsed.get("max_length"),
            word_count=parsed.get("word_count"),
            contains_character=parsed.get("contains_character"),
        )
    except HTTPException as e:
        # pass through error codes
        raise

    resp = {
        "data": response["data"],
        "count": response["count"],
        "interpreted_query": {
            "original": query,
            "parsed_filters": parsed
        }
    }
    return resp

@app.delete("/strings/{string_value}", status_code=204)
def delete_string(string_value: str = Path(...)):
    with Session(engine) as session:
        item = find_by_value(session, string_value)
        if not item:
            raise HTTPException(status_code=404, detail="String does not exist in the system")
        session.delete(item)
        session.commit()
    return JSONResponse(status_code=204, content=None)

