"""
test_triage.py — run from the project root (ahamnity/)
Server must be running: cd backend && uvicorn main:app --reload --port 8000
"""
import asyncio
import httpx

BASE = "http://localhost:9009"

TEST_CASES = [
    {
        "symptoms": "I have a mild headache and runny nose since yesterday",
        "language": "en",
        "expected": "low",
        "label": "Mild cold (English)",
    },
    {
        "symptoms": "mujhe do din se bukhaar hai aur pet mein dard hai",
        "language": "hi",
        "expected": "medium",
        "label": "Fever + stomach pain (Hindi)",
    },
    {
        "symptoms": "chest pain and cannot breathe properly",
        "language": "en",
        "expected": "high",
        "label": "Chest pain — emergency keyword scan",
    },
    {
        "symptoms": "meri maa behosh ho gayi hain",
        "language": "hi",
        "expected": "high",
        "label": "Unconscious — emergency keyword scan (Hindi)",
    },
]


async def test_risk_levels():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/api/triage/risk-levels")
        r.raise_for_status()
        print(f"  Risk levels endpoint OK ({len(r.json()['levels'])} levels)")
        print("  PASS")


async def test_assess(case: dict):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE}/api/triage/assess",
            json={"symptoms": case["symptoms"], "language": case["language"]},
        )
        r.raise_for_status()
        data = r.json()

    got = data["risk_level"]
    expected = case["expected"]
    status = "PASS" if got == expected else f"WARN (got {got.upper()}, expected {expected.upper()})"

    print(f"  [{got.upper()}] {case['label']}")
    print(f"  Advice: {data['advice'][:90]}...")
    # Safety phrase checks
    assert "not a substitute" in data["advice"], "Missing disclaimer!"
    if got == "low":
        assert "ASHA worker" in data["advice"] or "PHC" in data["advice"], "Missing low-risk phrase!"
    if got in ("medium", "high"):
        assert "emergency" in data["advice"].lower(), "Missing high-risk phrase!"
    print(f"  Safety phrases: OK  |  {status}")
    print()


async def main():
    print("\n=== Triage Agent Tests ===\n")

    print("1. Risk levels endpoint:")
    await test_risk_levels()

    print("\n2. Assessment cases:")
    for case in TEST_CASES:
        await test_assess(case)

    print("Done.")


asyncio.run(main())
