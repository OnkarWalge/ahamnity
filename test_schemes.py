"""
Test the scheme agent.
Usage: python test_schemes.py
Server must be running: cd backend && uvicorn main:app --reload --port 9009
"""
import asyncio
import httpx

BASE = "http://localhost:9009"

TEST_CASES = [
    {
        "name": "TB symptoms (Hindi)",
        "payload": {"symptoms": "mujhe khansi hai aur TB ka shak hai", "language": "hi"},
        "expect_id": "nikshay_poshan",
    },
    {
        "name": "Pregnancy (English)",
        "payload": {"symptoms": "I am pregnant and need delivery support", "language": "en",
                    "patient_gender": "female"},
        "expect_id": "janani_suraksha",
    },
    {
        "name": "Child fever (Hindi)",
        "payload": {"symptoms": "mere bache ko bukhaar hai", "language": "hi",
                    "patient_age": 5},
        "expect_id": "rashtriya_bal_swasthya",
    },
    {
        "name": "Surgery needed (English)",
        "payload": {"symptoms": "I need hospitalisation for surgery", "language": "en"},
        "expect_id": "pmjay",
    },
    {
        "name": "No keyword match — fallback",
        "payload": {"symptoms": "headache and mild fever", "language": "en"},
        "expect_id": "pmjay",  # fallback to universal schemes
    },
]


async def main():
    print("\n=== Scheme Agent Tests ===\n")

    async with httpx.AsyncClient(timeout=10.0) as client:

        # Test /all endpoint
        r = await client.get(f"{BASE}/api/schemes/all")
        print(f"1. All schemes: {r.json()['total']} loaded  {'PASS' if r.status_code == 200 else 'FAIL'}\n")

        # Test /match endpoint
        print("2. Matching cases:")
        for case in TEST_CASES:
            r = await client.post(f"{BASE}/api/schemes/match", json=case["payload"])
            if r.status_code != 200:
                print(f"  [{case['name']}] ERROR {r.status_code}: {r.text[:100]}")
                continue

            data = r.json()
            schemes = data["matched_schemes"]
            ids = [s.get("id", "") for s in schemes]
            matched = case["expect_id"] in ids
            names = [s["name"] for s in schemes]

            status = "PASS" if matched else "⚠️  MISMATCH"
            print(f"  [{case['name']}] {status}")
            print(f"    Got: {', '.join(names[:2])}")
            if not matched:
                print(f"    Expected scheme id '{case['expect_id']}' in results")

    print("\nDone.")


asyncio.run(main())