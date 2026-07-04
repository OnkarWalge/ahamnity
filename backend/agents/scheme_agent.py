import json
import logging
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
logger = logging.getLogger(__name__)
router = APIRouter()

# Load schemes once at startup
SCHEMES_PATH = Path(__file__).parent.parent / "data" / "schemes.json"
with open(SCHEMES_PATH, encoding="utf-8") as f:
    ALL_SCHEMES: List[dict] = json.load(f)

# Transliterated Hindi/Marathi → English keyword mappings
VERNACULAR_MAP = {
    "garbh": "pregnancy", "garbhvati": "pregnancy", "prasav": "delivery",
    "delivery": "delivery", "khansi": "cough", "khasi": "cough",
    "tb": "tuberculosis", "bacha": "child", "bachcha": "child",
    "bache": "child", "bachche": "child", "bacche": "child",
    "shishu": "infant", "bal": "child", "operation": "surgery",
    "aspatal": "hospitalisation", "hospital": "hospitalisation",
    "bukhaar": "fever", "bukhar": "fever", "tap": "fever",
    "cancer": "cancer", "kidney": "kidney",
}

MAX_RESULTS = 3


class SchemeRequest(BaseModel):
    symptoms: str
    language: Optional[str] = "hi"
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None


def _normalise(text: str) -> str:
    """Lowercase + replace known vernacular terms with English equivalents."""
    text = text.lower()
    for word, replacement in VERNACULAR_MAP.items():
        text = text.replace(word, replacement)
    return text


CHILD_KEYWORDS = {"child", "baby", "infant", "bal"}

def _score(scheme: dict, text: str) -> int:
    """Score a scheme by how many of its keywords appear in the normalised text."""
    score = 0
    for kw in scheme.get("keywords", []):
        if kw.lower() in text:
            score += 2

    # RBSK must have a child keyword — fever alone is too generic
    if scheme.get("id") == "rashtriya_bal_swasthya":
        has_child = any(kw in text for kw in CHILD_KEYWORDS)
        if not has_child:
            return 0

    return score


def _should_include(scheme: dict, age: Optional[int], gender: Optional[str]) -> bool:
    """Filter out schemes clearly not applicable to this patient."""
    if scheme["id"] == "rashtriya_bal_swasthya":
        if age is not None and age > 18:
            return False
    if scheme["id"] == "janani_suraksha":
        if gender is not None and gender.lower() in ("male", "m", "purush"):
            return False
    return True


def match_schemes(symptoms: str, age: Optional[int] = None, gender: Optional[str] = None) -> List[dict]:
    """
    Match symptoms to schemes. Returns up to MAX_RESULTS schemes by relevance.
    Falls back to universal schemes if no keywords match.
    """
    normalised = _normalise(symptoms)

    scored = []
    for scheme in ALL_SCHEMES:
        if not _should_include(scheme, age, gender):
            continue
        s = _score(scheme, normalised)
        if s > 0:
            scored.append((s, scheme))

    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        # Fallback: return the two universal schemes
        fallback_ids = {"pmjay", "mahatma_jyotirao_phule"}
        return [s for s in ALL_SCHEMES if s["id"] in fallback_ids][:2]

    return [scheme for _, scheme in scored[:MAX_RESULTS]]


@router.post("/match")
async def match_schemes_endpoint(request: SchemeRequest):
    """Match patient symptoms to relevant government health schemes."""
    if not request.symptoms.strip():
        raise HTTPException(status_code=400, detail="symptoms cannot be empty")

    try:
        matched = match_schemes(
            symptoms=request.symptoms,
            age=request.patient_age,
            gender=request.patient_gender,
        )
    except Exception as e:
        logger.error(f"Scheme matching error: {e}")
        raise HTTPException(status_code=500, detail=f"Scheme matching failed: {str(e)}")

    logger.info(f"Schemes | matched={len(matched)} | lang={request.language}")

    return {
        "matched_schemes": matched,
        "total_matched": len(matched),
        "note": "Eligibility confirmation required at your nearest PHC or CSC centre.",
    }


@router.get("/all")
async def list_all_schemes():
    """Return all schemes in the database."""
    return {"schemes": ALL_SCHEMES, "total": len(ALL_SCHEMES)}