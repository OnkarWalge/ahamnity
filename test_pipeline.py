"""
test_pipeline.py — run from the project root (ahamnity/)
Server must be running: cd backend && uvicorn main:app --reload --port 9009

For a real end-to-end test, record yourself speaking symptoms in Hindi/English
and save as test_audio.wav in the project root.
"""
import asyncio
import base64
import io
import os
import struct
import wave

import httpx

BASE = "http://localhost:9009"


def make_silent_wav(duration_sec: float = 1.0) -> bytes:
    """Creates a minimal valid WAV file with silence — for smoke testing."""
    sample_rate = 16000
    samples = int(sample_rate * duration_sec)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(struct.pack(f"<{samples}h", *([0] * samples)))
    return buf.getvalue()


async def test_pipeline():
    audio_file = "test_audio.wav"

    if os.path.exists(audio_file):
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()
        print(f"  Using real audio: {audio_file} ({len(audio_bytes):,} bytes)")
        using_real = True
    else:
        audio_bytes = make_silent_wav(1.0)
        print("  No test_audio.wav found — using silent stub")
        print("  (Record a WAV of yourself describing symptoms for a real test)")
        using_real = False

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{BASE}/api/pipeline/run",
            files={"audio": ("audio.wav", audio_bytes, "audio/wav")},
            data={"language": "hi"},
        )

    if not using_real:
        if r.status_code in (422, 502):
            detail = r.json().get("detail", "")
            print(f"\n  {r.status_code} received (expected for silent audio)")
            print(f"  Reason: {str(detail)[:120]}")
            print("  Pipeline endpoint is live and responding correctly.")
            print("  PASS (smoke test — use real audio for full end-to-end test)")
            return

    r.raise_for_status()
    data = r.json()

    print(f"\n  Transcription:  {data['transcription']}")
    print(f"  Language:       {data['detected_language']}")
    print(f"  Risk level:     {data['risk_level'].upper()}")
    print(f"  Advice:         {data['advice'][:100]}...")

    audio_out = base64.b64decode(data["audio_base64"])
    with open("test_pipeline_output.mp3", "wb") as f:
        f.write(audio_out)
    print(f"  Audio:          {len(audio_out):,} bytes -> test_pipeline_output.mp3")
    print(f"  Timestamp:      {data['timestamp']}")

    assert data["risk_level"] in ("low", "medium", "high"), "Invalid risk level"
    assert "not a substitute" in data["advice"], "Missing safety disclaimer"
    assert len(audio_out) > 1000, "Audio response too short"

    print("\n  PASS — full pipeline working end to end")


async def main():
    print("\n=== Pipeline End-to-End Test ===\n")
    await test_pipeline()
    print("\nDone.")


asyncio.run(main())
