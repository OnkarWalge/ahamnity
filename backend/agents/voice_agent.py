import os
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from groq import AsyncGroq

router = APIRouter()

SUPPORTED_LANGUAGES = {
    "hi": "Hindi",
    "mr": "Marathi",
    "en": "English",
    "bn": "Bengali",
    "te": "Telugu",
    "ta": "Tamil",
    "auto": "Auto-detect",
}

# Maps browser/OS MIME types to extensions Whisper accepts
CONTENT_TYPE_TO_EXT = {
    "audio/webm": "webm",
    "audio/mp4": "mp4",
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/x-m4a": "m4a",
    "audio/m4a": "m4a",
    "audio/ogg": "ogg",
    "application/octet-stream": "webm",  # safe fallback
}


async def transcribe_bytes(audio_bytes: bytes, content_type: str, language: str) -> dict:
    """
    Core transcription function.
    Called directly by the pipeline — not just the HTTP endpoint.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in .env")

    ext = CONTENT_TYPE_TO_EXT.get(content_type, "webm")
    client = AsyncGroq(api_key=api_key)

    transcription = await client.audio.transcriptions.create(
        file=(f"audio.{ext}", audio_bytes, content_type),
        model="whisper-large-v3",
        language=language if language != "auto" else None,
    )

    return {
        "text": transcription.text.strip(),
        "language": language,
    }


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(default="hi"),
):
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{language}'. Supported: {list(SUPPORTED_LANGUAGES.keys())}",
        )

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        result = await transcribe_bytes(
            audio_bytes,
            audio.content_type or "audio/webm",
            language,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Transcription failed: {str(e)}")

    return result


@router.get("/languages")
async def list_languages():
    return {
        "languages": [
            {"code": code, "name": name}
            for code, name in SUPPORTED_LANGUAGES.items()
            if code != "auto"
        ]
    }
