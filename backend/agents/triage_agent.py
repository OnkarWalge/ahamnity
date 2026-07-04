import os
import httpx
import asyncio
import re
from fastapi import APIRouter, HTTPException
from agents.red_flag import check_red_flags
from schemas.models import TriageRequest

router = APIRouter()



def check_emergency(text: str) -> bool:
    t = text.lower()
    return any(kw.lower() in t for kw in EMERGENCY_KEYWORDS)


# ---------------------------------------------------------------------------
# LLM prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a health triage assistant for rural India.
Assess the patient's symptoms and respond ONLY in this exact format — no extra text:

RISK_LEVEL: [LOW|MEDIUM|HIGH]
ADVICE: [your advice here, max 80 words]

Rules:
- LOW: mild symptoms, safe to manage at home for 24 hours
- MEDIUM: needs PHC visit within 24 hours
- HIGH: needs emergency hospital care immediately
- When uncertain between two levels, always choose the HIGHER one
- Never use the word "diagnosis" — use "assessment" instead
- Respond in the same language the patient used
- Keep advice practical for someone in rural India with limited resources"""


# ---------------------------------------------------------------------------
# Response processing
# ---------------------------------------------------------------------------
def inject_safety_phrases(risk_level: str, advice: str) -> str:
    """Guarantees mandatory safety phrases are present in every response."""
    disclaimer = "This is not a substitute for professional medical advice."
    low_phrase = (
        "If symptoms worsen or persist beyond 24 hours, "
        "contact your ASHA worker or visit the nearest PHC."
    )
    high_phrase = "Go to the nearest emergency department immediately."

    if risk_level == "low":
        if low_phrase not in advice:
            advice += f" {low_phrase}"
    elif risk_level in ("medium", "high"):
        if not advice.lower().startswith("go to the nearest emergency"):
            advice = f"{high_phrase} {advice}"

    if disclaimer not in advice:
        advice += f" {disclaimer}"

    return advice.strip()


def parse_llm_response(raw: str) -> dict:
    """
    Parses structured LLM output using regex instead of line position —
    different models put RISK_LEVEL/ADVICE on the same line or separate
    lines inconsistently, so position-based parsing isn't reliable across
    providers. Defaults to 'medium' on any parse failure — never silently
    drops to 'low'.
    """
    risk_level = "medium"

    risk_match = re.search(r"RISK_LEVEL:\s*(LOW|MEDIUM|HIGH)", raw, re.IGNORECASE)
    if risk_match:
        risk_level = risk_match.group(1).lower()

    advice_match = re.search(r"ADVICE:\s*(.*)", raw, re.IGNORECASE | re.DOTALL)
    advice = advice_match.group(1).strip() if advice_match else raw.strip()

    advice = inject_safety_phrases(risk_level, advice)
    return {"risk_level": risk_level, "advice": advice, "keywords": []}


# ---------------------------------------------------------------------------
# Core function (used by pipeline AND the HTTP endpoint)
# ---------------------------------------------------------------------------
async def assess_text(symptoms: str, language: str) -> dict:
    """
    Runs triage assessment.
    Emergency keyword scan runs first — LLM is only called if no emergency is detected.
    """
    red_flag_result = check_red_flags(symptoms)
    if red_flag_result["is_emergency"]:
        advice = inject_safety_phrases(
            "high",
            "Your symptoms may indicate a life-threatening emergency.",
        )
        return {
            "risk_level": "high",
            "advice": advice,
            "keywords": red_flag_result["flags_found"],
        }

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in .env")

    MAX_RETRIES = 3
    BACKOFF_SECONDS = [2, 5, 10]

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(
                    "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"Patient symptoms: {symptoms}"},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 300,
                    },
                )
                resp.raise_for_status()

            data = resp.json()
            raw_response = data["choices"][0]["message"]["content"].strip()
            return parse_llm_response(raw_response)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < MAX_RETRIES - 1:
                await asyncio.sleep(BACKOFF_SECONDS[attempt])
                continue
            advice = inject_safety_phrases(
                "medium",
                "We could not fully assess your symptoms right now. "
                "Please visit your nearest PHC or contact your ASHA worker.",
            )
            return {"risk_level": "medium", "advice": advice, "keywords": []}

        except httpx.TimeoutException:
            advice = inject_safety_phrases(
                "medium",
                "We could not fully assess your symptoms. "
                "Please visit your nearest PHC or contact your ASHA worker.",
            )
            return {"risk_level": "medium", "advice": advice, "keywords": []}


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------
@router.post("/assess")
async def assess(request: TriageRequest):
    try:
        result = await assess_text(request.symptoms, request.language)
        result["language"] = request.language
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Triage failed: {str(e)}")


@router.get("/risk-levels")
async def risk_levels():
    return {
        "levels": [
            {
                "level": "low",
                "description": "Mild symptoms — safe to manage at home",
                "action": "Monitor at home. Contact ASHA worker if worsening.",
            },
            {
                "level": "medium",
                "description": "Moderate symptoms — PHC visit within 24 hours",
                "action": "Visit nearest Primary Health Centre today.",
            },
            {
                "level": "high",
                "description": "Serious symptoms — emergency care required",
                "action": "Go to nearest emergency department immediately.",
            },
        ]
    }
