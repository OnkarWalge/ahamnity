"""
Step 14 — Full Integration Test

Chains Triage -> Red Flag -> Schemes -> Locator -> TTS -> Case Storage
together for 3 realistic scenarios (low/medium/high risk, 2 languages).

This validates that every backend agent interoperates correctly end-to-end.
It deliberately bypasses real microphone audio (Voice/Whisper was already
validated standalone in Step 2 and live via browser in Step 10) so this
test can be re-run anytime in seconds without needing a recording.

Usage: python test_integration.py
Server must be running: cd backend && uvicorn main:app --reload --port 9009
"""
import asyncio
import httpx

BASE = "http://localhost:9009"

# Fixed test location: Nanded, Maharashtra (used consistently across all prior tests)
TEST_LAT, TEST_LNG = 19.1383, 77.3210

SCENARIOS = [
    {
        "name": "LOW risk — mild cold (English)",
        "symptoms": "I have a mild cold and a slight headache since yesterday",
        "language": "en",
        "expected_risk": "low",
    },
    {
        "name": "MEDIUM risk — persistent fever (Hindi)",
        "symptoms": "mujhe teen din se bukhar hai aur kamzori bhi hai",
        "language": "hi",
        "expected_risk": "medium",
    },
    {
        "name": "HIGH risk — chest pain, red flag override (English)",
        "symptoms": "I have severe chest pain and difficulty breathing",
        "language": "en",
        "expected_risk": "high",
    },
]


async def run_scenario(client: httpx.AsyncClient, scenario: dict) -> bool:
    print(f"\n{'='*65}")
    print(f"  {scenario['name']}")
    print(f"{'='*65}")
    all_ok = True

    # 1. Red Flag check (independent confirmation)
    r = await client.post(f"{BASE}/api/redflag/check", json={"text": scenario["symptoms"]})
    redflag = r.json()
    print(f"  1. Red Flag      | is_emergency={redflag['is_emergency']} | categories={redflag['categories']}")

    # 2. Triage assessment (red flag runs internally here too)
    r = await client.post(
        f"{BASE}/api/triage/assess",
        json={"symptoms": scenario["symptoms"], "language": scenario["language"]},
    )
    if r.status_code != 200:
        print(f"  2. Triage        | FAIL — HTTP {r.status_code}: {r.text[:150]}")
        return False
    triage = r.json()
    risk_ok = triage["risk_level"] == scenario["expected_risk"]
    print(f"  2. Triage        | risk={triage['risk_level']} (expected {scenario['expected_risk']}) "
          f"{'OK' if risk_ok else 'MISMATCH'}")
    all_ok = all_ok and risk_ok

    disclaimer_ok = "not a substitute" in triage["advice"].lower()
    print(f"     Safety phrase | disclaimer present: {disclaimer_ok}")
    all_ok = all_ok and disclaimer_ok

    # 3. Scheme matching
    r = await client.post(
        f"{BASE}/api/schemes/match",
        json={"symptoms": scenario["symptoms"], "language": scenario["language"]},
    )
    schemes = r.json()
    schemes_ok = schemes["total_matched"] > 0
    print(f"  3. Schemes       | matched={schemes['total_matched']} "
          f"{'OK' if schemes_ok else 'FAIL — expected at least fallback schemes'}")
    all_ok = all_ok and schemes_ok

    # 4. Locator
    r = await client.get(
        f"{BASE}/api/locator/nearby",
        params={"lat": TEST_LAT, "lng": TEST_LNG, "radius_km": 15},
    )
    phcs = r.json()
    phcs_ok = phcs["total_found"] > 0
    print(f"  4. Locator       | found={phcs['total_found']} "
          f"{'OK' if phcs_ok else 'FAIL — check GOOGLE_MAPS_API_KEY'}")
    all_ok = all_ok and phcs_ok

    # 5. TTS — synthesize the ACTUAL generated advice, not a canned string
    r = await client.post(
        f"{BASE}/api/tts/synthesize",
        json={"text": triage["advice"], "language": scenario["language"]},
    )
    tts_ok = r.status_code == 200 and len(r.json().get("audio_base64", "")) > 0
    print(f"  5. TTS           | {'OK — audio generated' if tts_ok else 'FAIL'}")
    all_ok = all_ok and tts_ok

    # 6. Save case (what the pipeline does automatically)
    r = await client.post(
        f"{BASE}/api/cases/",
        json={
            "transcript": scenario["symptoms"],
            "language": scenario["language"],
            "risk_level": triage["risk_level"],
            "advice": triage["advice"],
            "red_flags": triage.get("keywords", []),
            "district": "Nanded",
        },
    )
    case_ok = r.status_code == 200
    case_id = r.json().get("id") if case_ok else None
    print(f"  6. Case Save     | {'OK — id=' + str(case_id) if case_ok else 'FAIL'}")
    all_ok = all_ok and case_ok

    # 7. Round-trip confirm
    if case_id:
        r = await client.get(f"{BASE}/api/cases/{case_id}")
        roundtrip_ok = r.status_code == 200 and r.json()["transcript"] == scenario["symptoms"]
        print(f"  7. Round-trip    | {'OK' if roundtrip_ok else 'FAIL'}")
        all_ok = all_ok and roundtrip_ok

    print(f"\n  >>> {'PASS' if all_ok else 'FAIL'} — {scenario['name']}")
    return all_ok


async def main():
    print("\n" + "=" * 65)
    print("  STEP 14 — FULL INTEGRATION TEST")
    print("=" * 65)
    print("  Chains: Red Flag -> Triage -> Schemes -> Locator -> TTS -> Cases")
    print("  Note: bypasses real audio — Voice/Whisper validated separately.")

    results = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, scenario in enumerate(SCENARIOS):
            if i > 0:
                # OpenRouter's free tier rate-limits rapid back-to-back calls —
                # this pause keeps the test stable, it's not masking a real bug.
                await asyncio.sleep(6)
            ok = await run_scenario(client, scenario)
            results.append(ok)

    print("\n" + "=" * 65)
    passed = sum(results)
    print(f"  RESULT: {passed}/{len(results)} scenarios fully passed")
    print("=" * 65)

    if passed == len(results):
        print("\n  All backend agents are correctly wired end-to-end.")
        print("  Remaining manual checks: live voice + mobile UI (see checklist).")
    else:
        print("\n  Review the FAIL lines above before proceeding to deployment.")


asyncio.run(main())