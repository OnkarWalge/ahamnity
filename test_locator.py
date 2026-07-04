"""
Test the locator agent.
Usage:
  python test_locator.py           # tests Nanded, Maharashtra (default)
  python test_locator.py <lat> <lng>  # custom coordinates

Server must be running: cd backend && uvicorn main:app --reload --port 9009
Requires: GOOGLE_MAPS_API_KEY in backend/.env
"""
import asyncio
import sys
import httpx

BASE = "http://localhost:9009"


async def test_nearby(lat: float, lng: float, radius_km: int = 15):
    print(f"\n=== Locator Agent Test ===")
    print(f"  Searching {radius_km}km around ({lat}, {lng})\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            f"{BASE}/api/locator/nearby",
            params={"lat": lat, "lng": lng, "radius_km": radius_km},
        )

    if r.status_code != 200:
        print(f"  ERROR {r.status_code}: {r.text[:300]}")
        return

    data = r.json()
    phcs = data.get("phcs", [])

    if not phcs:
        print(f"  No PHCs found. Message: {data.get('message', '')}")
        return

    print(f"  Found {data['total_found']} PHC(s):\n")
    for i, phc in enumerate(phcs, 1):
        print(f"  {i}. {phc['name']}")
        print(f"     Address  : {phc['address']}")
        print(f"     Distance : {phc['distance_km']} km")
        print(f"     Phone    : {phc.get('phone') or 'Not available'}")
        open_now = phc.get('open_now')
        if open_now is not None:
            print(f"     Open now : {'Yes' if open_now else 'No'}")
        print(f"     Maps     : {phc['maps_url']}")
        print()

    print("  PASS")


async def main():
    # Default: Nanded, Maharashtra — good test for rural PHC density
    lat = float(sys.argv[1]) if len(sys.argv) > 1 else 19.1383
    lng = float(sys.argv[2]) if len(sys.argv) > 2 else 77.3210
    await test_nearby(lat, lng)


asyncio.run(main())