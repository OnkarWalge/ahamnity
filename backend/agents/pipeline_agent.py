import base64
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from agents.voice_agent import transcribe_bytes
from agents.triage_agent import assess_text
from tts.tts_engine import synthesize_speech
from database.supabase_client import create_case

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run")
async def run_pipeline(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(default="hi"),
    patient_age: Optional[int] = Form(default=None),
    patient_gender: Optional[str] = Form(default=None),
    district: Optional[str] = Form(default=None),
    patient_phone: Optional[str] = Form(default=None),
    latitude: Optional[float] = Form(default=None),
    longitude: Optional[float] = Form(default=None),
):
    """
    Full triage pipeline in one API call.

    Input:  audio file + language code + optional patient context
    Output: transcription, risk level, advice text, advice audio, case_id

    Flow: audio -> Groq Whisper STT -> OpenRouter LLM triage -> edge-tts -> Supabase save -> JSON
    """
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file received")

    # Step 1: Speech to text
    try:
        transcription = await transcribe_bytes(
            audio_bytes,
            audio.content_type or "audio/webm",
            language,
        )
        symptoms_text = transcription["text"].strip()
        detected_language = transcription.get("language", language)
        if not symptoms_text:
            raise HTTPException(
                status_code=422,
                detail="No speech detected. Please speak clearly and try again.",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not process audio: {str(e)}")

    # Step 2: Triage assessment (red flag scan + LLM)
    try:
        triage = await assess_text(symptoms_text, detected_language)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Triage error: {str(e)}")

    # Step 3: Synthesise advice as audio
    try:
        audio_response = await synthesize_speech(triage["advice"], detected_language)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TTS error: {str(e)}")

    # Step 4: Save case to Supabase — best effort.
    # A database hiccup must NEVER block the patient from getting their result,
    # so any failure here is logged and swallowed, not raised.
    case_id = None
    try:
        case_payload = {
            "transcript": symptoms_text,
            "language": detected_language,
            "risk_level": triage["risk_level"],
            "advice": triage["advice"],
            "red_flags": triage.get("keywords", []),
            "patient_age": patient_age,
            "patient_gender": patient_gender,
            "district": district,
            "patient_phone": patient_phone,
            "latitude": latitude,
            "longitude": longitude,
        }
        # Drop None values — Supabase doesn't need explicit nulls for optional columns
        case_payload = {k: v for k, v in case_payload.items() if v is not None}

        saved = await create_case(case_payload)
        if saved:
            case_id = saved["id"]
    except Exception as e:
        logger.error(f"Case save failed (non-blocking): {e}")

    return {
        "case_id": case_id,
        "transcription": symptoms_text,
        "detected_language": detected_language,
        "risk_level": triage["risk_level"],
        "advice": triage["advice"],
        "keywords": triage.get("keywords", []),
        "audio_base64": base64.b64encode(audio_response).decode("utf-8"),
        "audio_format": "mp3",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
