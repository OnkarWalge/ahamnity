"""
Test Supabase case storage.
Usage: python test_supabase.py
Server must be running: cd backend && uvicorn main:app --reload --port 9009
Requires: SUPABASE_URL and SUPABASE_KEY in backend/.env
Requires: cases table created via backend/database/schema.sql (run in Supabase SQL Editor)
"""
import asyncio
import httpx

BASE = "http://localhost:9009"


async def main():
    print("\n=== Supabase Case Storage Test ===\n")

    async with httpx.AsyncClient(timeout=15.0) as client:

        # 1. Create a case
        print("1. Creating a case...")
        payload = {
            "transcript": "mujhe 3 din se bukhar hai",
            "language": "hi",
            "risk_level": "medium",
            "advice": "Visit your nearest PHC within 24 hours. This is not a substitute for professional medical advice.",
            "red_flags": [],
            "patient_age": 34,
            "patient_gender": "female",
            "district": "Nanded",
        }
        r = await client.post(f"{BASE}/api/cases/", json=payload)
        if r.status_code != 200:
            print(f"  ERROR {r.status_code}: {r.text[:300]}")
            return

        case = r.json()
        case_id = case["id"]
        print(f"  PASS — created case_id={case_id}")
        print(f"  risk_level={case['risk_level']}  district={case.get('district')}\n")

        # 2. Fetch it back
        print("2. Fetching case by id...")
        r = await client.get(f"{BASE}/api/cases/{case_id}")
        if r.status_code == 200:
            print(f"  PASS — transcript matches: {r.json()['transcript'] == payload['transcript']}\n")
        else:
            print(f"  ERROR {r.status_code}: {r.text[:200]}\n")

        # 3. List recent cases
        print("3. Listing recent cases...")
        r = await client.get(f"{BASE}/api/cases/", params={"limit": 10})
        if r.status_code == 200:
            data = r.json()
            print(f"  PASS — found {data['total']} case(s) in table\n")
        else:
            print(f"  ERROR {r.status_code}: {r.text[:200]}\n")

        # 4. Update ASHA notification flag
        print("4. Marking asha_notified=True...")
        r = await client.patch(f"{BASE}/api/cases/{case_id}", json={"asha_notified": True})
        if r.status_code == 200:
            print(f"  PASS — asha_notified={r.json()['asha_notified']}\n")
        else:
            print(f"  ERROR {r.status_code}: {r.text[:200]}\n")

        # 5. Filter by risk_level
        print("5. Filtering by risk_level=medium...")
        r = await client.get(f"{BASE}/api/cases/", params={"risk_level": "medium"})
        if r.status_code == 200:
            print(f"  PASS — {r.json()['total']} medium-risk case(s)\n")

    print("Done. Check your Supabase Table Editor → cases table to see the row.")


asyncio.run(main())