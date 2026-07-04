"""
test_tts.py — run from the project root (ahamnity/)
Server must be running: cd backend && uvicorn main:app --reload --port 8000
Saves .mp3 files to project root — open them to verify audio quality.
"""
import asyncio
import base64
import httpx

BASE = "http://localhost:9009"

TEST_CASES = [
    {
        "text": "aapke lakshan halke hain. agar 24 ghante mein sudhar na ho to ASHA worker se milein.",
        "language": "hi",
        "label": "Hindi",
    },
    {
        "text": "Your symptoms appear mild. Please rest and stay hydrated. If symptoms worsen, visit the nearest PHC.",
        "language": "en",
        "label": "English",
    },
    {
        "text": "tumchi lakshane saumya aahet. ASHA karyakartya shi sampark sadha.",
        "language": "mr",
        "label": "Marathi",
    },
]


async def test_voices():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/api/tts/voices")
        r.raise_for_status()
        voices = r.json()["voices"]
        print(f"  {len(voices)} voices configured:")
        for v in voices:
            print(f"    {v['language_code']} -> {v['voice_name']}  (free={v['api_key_required'] == False})")
        print("  PASS")


async def test_synthesize(text: str, language: str, label: str):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE}/api/tts/synthesize",
            json={"text": text, "language": language},
        )
        r.raise_for_status()
        data = r.json()

    audio = base64.b64decode(data["audio_base64"])
    assert len(audio) > 1000, "Audio too short — something went wrong"

    out = f"test_tts_{language}.mp3"
    with open(out, "wb") as f:
        f.write(audio)
    print(f"  [{label}] {len(audio):,} bytes -> {out}  PASS")


async def main():
    print("\n=== TTS Engine Tests (edge-tts) ===\n")

    print("1. Voices endpoint:")
    await test_voices()

    print("\n2. Synthesis:")
    for tc in TEST_CASES:
        await test_synthesize(tc["text"], tc["language"], tc["label"])

    print("\nOpen the .mp3 files to verify audio quality.")
    print("Done.")


asyncio.run(main())
