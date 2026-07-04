import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Categorised emergency keywords — single source of truth for the whole app.
# triage_agent.py imports check_red_flags() from this module instead of
# keeping its own copy, so there is exactly one list to maintain.
#
# Each category has a short human-readable reason used in the override
# message and in ASHA-facing logs/dashboards later.
# ---------------------------------------------------------------------------
RED_FLAG_CATEGORIES = {
    "cardiac": {
        "reason": "Possible heart attack symptoms",
        "keywords": [
            "chest pain", "chest pressure", "chest tightness",
            "seene mein dard", "chest mein dard",
            "\u0926\u093f\u0932 \u0915\u093e \u0926\u094c\u0930\u093e",  # दिल का दौरा
            "heart attack", "dil ka daura",
        ],
    },
    "respiratory": {
        "reason": "Severe breathing difficulty",
        "keywords": [
            "can't breathe", "cannot breathe", "not breathing",
            "difficulty breathing", "shortness of breath",
            "saans nahi aa rahi", "saans nahi le pa raha",
            "\u0938\u093e\u0902\u0938 \u0928\u0939\u0940\u0902",  # सांस नहीं
            "\u0936\u094d\u0935\u093e\u0938 \u0918\u0947\u0924\u093e \u092f\u0947\u0924 \u0928\u093e\u0939\u0940",
            "choking", "gala ghut raha",
        ],
    },
    "neurological": {
        "reason": "Possible stroke or loss of consciousness",
        "keywords": [
            "unconscious", "unresponsive", "not waking up",
            "stroke", "face drooping", "arm weakness", "slurred speech",
            "seizure", "convulsion", "fit aa raha",
            "hosh nahi", "behosh",
            "\u092c\u0947\u0939\u094b\u0936", "\u092c\u0947\u0936\u0941\u0926\u094d\u0927",  # बेहोश, बेशुद्ध
        ],
    },
    "bleeding": {
        "reason": "Severe or uncontrolled bleeding",
        "keywords": [
            "severe bleeding", "heavy bleeding", "won't stop bleeding",
            "vomiting blood", "coughing blood",
            "bahut khoon beh raha", "khoon nahi ruk raha",
            "\u0926\u094c\u0930\u093e \u092a\u095c", "\u062e\u0942\u0928 \u0915\u0940 \u0909\u0932\u094d\u091f\u0940",
        ],
    },
    "poisoning": {
        "reason": "Suspected poisoning, overdose, or venomous bite",
        "keywords": [
            "poisoning", "overdose", "swallowed poison",
            "snake bite", "scorpion bite", "dog bite rabies",
            "zahar khaya", "saanp ne kaata", "saanp ka kaatna",
        ],
    },
    "obstetric": {
        "reason": "Pregnancy-related emergency",
        "keywords": [
            "heavy bleeding pregnant", "baby not moving",
            "water broke bleeding", "severe labour pain early",
            "garbhvati khoon beh raha", "bachcha hil nahi raha pet mein",
            "premature labour", "convulsions pregnant", "eclampsia",
        ],
    },
    "pediatric": {
        "reason": "Newborn or infant emergency",
        "keywords": [
            "newborn fever", "infant fever", "baby not feeding",
            "baby blue lips", "infant not waking", "baby won't wake up",
            "naya janam fever", "bachcha doodh nahi pi raha",
            "infant convulsion", "baby seizure",
        ],
    },
    "allergic": {
        "reason": "Severe allergic reaction (anaphylaxis)",
        "keywords": [
            "severe allergic", "anaphylaxis", "throat swelling",
            "face swelling sudden", "allergic reaction breathing",
        ],
    },
    "mental_health": {
        "reason": "Risk of self-harm — needs immediate human support",
        "keywords": [
            "suicide", "suicidal", "want to die", "end my life",
            "khud ko khatam", "marna chahta hoon",
        ],
    },
}


class RedFlagCheckRequest(BaseModel):
    text: str
    language: Optional[str] = "hi"


def check_red_flags(text: str) -> dict:
    """
    Core detection function — pure, synchronous, no network calls.
    Called directly by triage_agent.py and pipeline_agent.py before any LLM call.

    Returns:
        {
            "is_emergency": bool,
            "flags_found": [keywords matched],
            "categories": [category names matched],
            "reasons": [human-readable reasons],
        }
    """
    text_lower = text.lower()
    flags_found = []
    categories = []
    reasons = []

    for category, info in RED_FLAG_CATEGORIES.items():
        for kw in info["keywords"]:
            if kw.lower() in text_lower:
                flags_found.append(kw)
                if category not in categories:
                    categories.append(category)
                    reasons.append(info["reason"])

    return {
        "is_emergency": len(flags_found) > 0,
        "flags_found": flags_found,
        "categories": categories,
        "reasons": reasons,
    }


def get_override_message(result: dict) -> Optional[str]:
    """
    Builds a short clinical reason string for logging / ASHA dashboard.
    Not the patient-facing advice text — triage_agent.py still owns that.
    """
    if not result["is_emergency"]:
        return None
    return "; ".join(result["reasons"])


# ---------------------------------------------------------------------------
# Standalone HTTP endpoints — useful for frontend pre-checks and debugging
# ---------------------------------------------------------------------------

@router.post("/check")
async def check_endpoint(request: RedFlagCheckRequest):
    """
    Runs the emergency keyword scan on arbitrary text.
    Frontend can call this directly for instant feedback before
    the full triage pipeline finishes (e.g. show a red banner immediately).
    """
    result = check_red_flags(request.text)
    result["override_message"] = get_override_message(result)
    logger.info(
        f"RedFlag check | emergency={result['is_emergency']} "
        f"| categories={result['categories']}"
    )
    return result


@router.get("/categories")
async def list_categories():
    """Returns all emergency categories and example keywords — for documentation/UI."""
    return {
        "categories": [
            {
                "name": cat,
                "reason": info["reason"],
                "keyword_count": len(info["keywords"]),
            }
            for cat, info in RED_FLAG_CATEGORIES.items()
        ],
        "total_keywords": sum(len(i["keywords"]) for i in RED_FLAG_CATEGORIES.values()),
    }