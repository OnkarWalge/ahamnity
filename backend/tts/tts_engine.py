import io
import asyncio
import base64
import logging

import edge_tts
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Microsoft Neural voices for all 6 supported languages
VOICE_MAP = {
    "hi": "hi-IN-SwaraNeural",     # Hindi
    "mr": "mr-IN-AarohiNeural",    # Marathi
    "en": "en-US-JennyNeural",     # English
    "bn": "bn-IN-TanishaaNeural",  # Bengali
    "te": "te-IN-ShrutiNeural",    # Telugu
    "ta": "ta-IN-PallaviNeural",   # Tamil
}
DEFAULT_VOICE = "en-US-JennyNeural"
SPEECH_RATE = "-10%"  # Slightly slower for accessibility and rural comprehension


class TTSRequest(BaseModel):
    text: str
    language: str = "en"


MAX_TTS_RETRIES = 3
RETRY_BACKOFF_SECONDS = [0.8, 1.6, 3.0]  # one entry per retry attempt


async def synthesize_speech(text: str, language: str) -> bytes:
    """
    Core TTS function.
    Called directly by the pipeline — not just the HTTP endpoint.
    Returns raw MP3 bytes.

    edge-tts's free websocket endpoint occasionally rejects connections
    (403 / connection drop) under transient load. Most of these resolve
    on an immediate retry, so we retry a few times with short backoff
    before giving up — this keeps a single flaky connection invisible
    to the patient instead of surfacing as an error screen.
    """
    voice = VOICE_MAP.get(language, DEFAULT_VOICE)
    last_error = None

    for attempt in range(MAX_TTS_RETRIES):
        try:
            communicate = edge_tts.Communicate(text, voice, rate=SPEECH_RATE)
            buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])

            audio_bytes = buffer.getvalue()
            if not audio_bytes:
                raise RuntimeError("edge-tts returned empty audio")

            if attempt > 0:
                logger.info(f"TTS succeeded on retry attempt {attempt + 1}")
            return audio_bytes

        except Exception as e:
            last_error = e
            logger.warning(f"TTS attempt {attempt + 1}/{MAX_TTS_RETRIES} failed: {e}")
            if attempt < MAX_TTS_RETRIES - 1:
                await asyncio.sleep(RETRY_BACKOFF_SECONDS[attempt])

    raise RuntimeError(
        f"edge-tts failed after {MAX_TTS_RETRIES} attempts: {last_error}"
    )


@router.post("/synthesize")
async def synthesize(request: TTSRequest):
    """Returns base64-encoded MP3 audio."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        audio_bytes = await synthesize_speech(request.text, request.language)
        return {
            "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
            "format": "mp3",
            "language": request.language,
            "voice": VOICE_MAP.get(request.language, DEFAULT_VOICE),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@router.post("/synthesize/stream")
async def synthesize_stream(request: TTSRequest):
    """Streams raw MP3 bytes directly — lower latency for frontend playback."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    voice = VOICE_MAP.get(request.language, DEFAULT_VOICE)

    async def audio_generator():
        communicate = edge_tts.Communicate(request.text, voice, rate=SPEECH_RATE)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]

    return StreamingResponse(audio_generator(), media_type="audio/mpeg")


@router.get("/voices")
async def list_voices():
    return {
        "voices": [
            {
                "language_code": lang,
                "voice_name": voice,
                "provider": "edge-tts (Microsoft Neural)",
                "api_key_required": False,
                "cost": "free",
            }
            for lang, voice in VOICE_MAP.items()
        ]
    }
