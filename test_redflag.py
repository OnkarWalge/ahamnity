"""
Test the red flag emergency detection module.
Usage: python test_redflag.py
Server must be running: cd backend && uvicorn main:app --reload --port 9009
"""
import asyncio
import httpx

BASE = "http://localhost:9009"

TEST_CASES = [
    {
        "name": "Chest pain (English)",
        "text": "I have severe chest pain and pressure",
        "expect_emergency": True,
        "expect_category": "cardiac",
    },
    {
        "name": "Heart attack (Hindi)",
        "text": "uska dil ka daura pad gaya hai",
        "expect_emergency": True,
        "expect_category": "cardiac",
    },
    {
        "name": "Breathing difficulty (English)",
        "text": "I cannot breathe properly since morning",
        "expect_emergency": True,
        "expect_category": "respiratory",
    },
    {
        "name": "Unconscious (Hindi script)",
        "text": "mera bhai \u092c\u0947\u0939\u094b\u0936 ho gaya hai",
        "expect_emergency": True,
        "expect_category": "neurological",
    },
    {
        "name": "Snake bite",
        "text": "saanp ne kaata hai mujhe",
        "expect_emergency": True,
        "expect_category": "poisoning",
    },
    {
        "name": "Pregnant heavy bleeding",
        "text": "garbhvati khoon beh raha hai bahut",
        "expect_emergency": True,
        "expect_category": "obstetric",
    },
    {
        "name": "Newborn not feeding",
        "text": "bachcha doodh nahi pi raha 2 din se",
        "expect_emergency": True,
        "expect_category": "pediatric",
    },
    {
        "name": "Mild cold — NOT emergency",
        "text": "I have a slight cough and runny nose",
        "expect_emergency": False,
        "expect_category": None,
    },
    {
        "name": "Mild headache — NOT emergency",
        "text": "mujhe thoda sa sar dard hai",
        "expect_emergency": False,
        "expect_category": None,
    },
]


async def main():
    print("\n=== Red Flag Detection Tests ===\n")

    async with httpx.AsyncClient(timeout=10.0) as client:

        # Categories endpoint
        r = await client.get(f"{BASE}/api/redflag/categories")
        data = r.json()
        print(f"1. Categories loaded: {len(data['categories'])} categories, "
              f"{data['total_keywords']} total keywords  PASS\n")

        # Detection cases
        print("2. Detection cases:")
        passed = 0
        for case in TEST_CASES:
            r = await client.post(f"{BASE}/api/redflag/check", json={"text": case["text"]})
            if r.status_code != 200:
                print(f"  [{case['name']}] ERROR {r.status_code}: {r.text[:100]}")
                continue

            result = r.json()
            is_match = result["is_emergency"] == case["expect_emergency"]
            cat_match = True
            if case["expect_category"]:
                cat_match = case["expect_category"] in result["categories"]

            status = "PASS" if (is_match and cat_match) else "⚠️  FAIL"
            if is_match and cat_match:
                passed += 1

            print(f"  [{case['name']}] {status}")
            print(f"    is_emergency: {result['is_emergency']}  categories: {result['categories']}")
            if result.get("override_message"):
                print(f"    reason: {result['override_message']}")

        print(f"\n  {passed}/{len(TEST_CASES)} cases passed")

    print("\nDone.")


asyncio.run(main())