"""
test_voice.py — run from the project root (ahamnity/)
Server must be running: cd backend && uvicorn main:app --reload --port 9009
"""
import asyncio
import os
import httpx

BASE = "http://localhost:9009"


async def test_languages():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/api/voice/languages")
        r.raise_for_status()
        langs = r.json()["languages"]
        codes = [l["code"] for l in langs]
        print(f"  Languages: {codes}")
        assert "hi" in codes and "en" in codes, "Missing expected languages"
        print("  PASS")


async def test_transcribe(filepath: str, language: str = "hi"):
    if not os.path.exists(filepath):
        print(f"  SKIP — no audio file at '{filepath}'")
        print("  To test: record a short WAV and save it as test_audio.wav")
        return

    async with httpx.AsyncClient(timeout=30) as client:
        with open(filepath, "rb") as f:
            r = await client.post(
                f"{BASE}/api/voice/transcribe",
                files={"audio": ("audio.wav", f, "audio/wav")},
                data={"language": language},
            )
        r.raise_for_status()
        data = r.json()
        print(f"  Transcribed: '{data['text']}'")
        print(f"  Language:    {data['language']}")
        print("  PASS")


async def main():
    print("\n=== Voice Agent Tests ===\n")

    print("1. Languages endpoint:")
    await test_languages()

    print("\n2. Transcription (needs test_audio.wav in project root):")
    await test_transcribe("test_audio.wav", "hi")

    print("\n Done.")


asyncio.run(main())
