import os
import logging
import httpx
from fastapi import APIRouter, HTTPException, Query
from dotenv import load_dotenv
from pathlib import Path
from math import radians, sin, cos, sqrt, atan2

load_dotenv(Path(__file__).parent.parent / ".env")
logger = logging.getLogger(__name__)
router = APIRouter()

# Places API (New) endpoints — different from legacy
NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"

MAX_RESULTS = 5
DEFAULT_RADIUS_M = 15000.0  # 15 km


def _get_api_key() -> str:
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="GOOGLE_MAPS_API_KEY not configured")
    return key


def _maps_url(place_id: str) -> str:
    return f"https://www.google.com/maps/place/?q=place_id:{place_id}"


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def _format_place(place: dict, user_lat: float, user_lng: float) -> dict:
    loc = place.get("location", {})
    lat = loc.get("latitude", 0)
    lng = loc.get("longitude", 0)
    distance_km = _haversine_km(user_lat, user_lng, lat, lng)

    # New API returns displayName as object
    name = place.get("displayName", {}).get("text", "Unknown")

    return {
        "name": name,
        "address": place.get("formattedAddress", "Address unavailable"),
        "latitude": lat,
        "longitude": lng,
        "distance_km": round(distance_km, 2),
        "place_id": place.get("id", ""),
        "maps_url": _maps_url(place.get("id", "")),
        "phone": place.get("nationalPhoneNumber"),
        "open_now": place.get("currentOpeningHours", {}).get("openNow"),
        "rating": place.get("rating"),
    }


async def _search_nearby(
    client: httpx.AsyncClient,
    lat: float,
    lng: float,
    radius_m: float,
    api_key: str,
    included_types: list[str],
) -> list[dict]:
    """
    Calls Places API (New) Nearby Search.
    Uses POST with JSON body + X-Goog-Api-Key header.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        # FieldMask controls which fields are returned (and billed)
        "X-Goog-FieldMask": (
            "places.id,"
            "places.displayName,"
            "places.formattedAddress,"
            "places.location,"
            "places.nationalPhoneNumber,"
            "places.currentOpeningHours.openNow,"
            "places.rating"
        ),
    }

    body = {
        "includedTypes": included_types,
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_m,
            }
        },
        "rankPreference": "DISTANCE",
    }

    try:
        resp = await client.post(NEARBY_URL, headers=headers, json=body, timeout=12.0)
        resp.raise_for_status()
        return resp.json().get("places", [])
    except httpx.TimeoutException:
        logger.warning("Places API (New) timeout")
        return []
    except httpx.HTTPStatusError as e:
        logger.error(f"Places API error {e.response.status_code}: {e.response.text[:200]}")
        return []


@router.get("/nearby")
async def find_nearby_phcs(
    lat: float = Query(..., description="Patient latitude", ge=-90, le=90),
    lng: float = Query(..., description="Patient longitude", ge=-180, le=180),
    radius_km: int = Query(default=15, description="Search radius in km", ge=1, le=50),
):
    """
    Find nearest PHCs / government hospitals using Places API (New).
    """
    api_key = _get_api_key()
    radius_m = float(radius_km * 1000)

    all_places: list[dict] = []

    async with httpx.AsyncClient() as client:
        # Search 1: hospitals (catches most PHCs)
        results = await _search_nearby(
            client, lat, lng, radius_m, api_key,
            included_types=["hospital"],
        )
        all_places.extend(results)

        # Search 2: health (catches clinics, health centres)
        if len(all_places) < MAX_RESULTS:
            results2 = await _search_nearby(
                client, lat, lng, radius_m, api_key,
                included_types=["health"],
            )
            # Deduplicate by place id
            existing_ids = {p.get("id") for p in all_places}
            for p in results2:
                if p.get("id") not in existing_ids:
                    all_places.append(p)
                    existing_ids.add(p.get("id"))

    if not all_places:
        return {
            "phcs": [],
            "total_found": 0,
            "query": {"lat": lat, "lng": lng, "radius_km": radius_km},
            "message": (
                "No health facilities found in this area. "
                "Try increasing the radius or contact your district health office."
            ),
        }

    # Sort by distance and take top N
    formatted = [_format_place(p, lat, lng) for p in all_places]
    formatted.sort(key=lambda x: x["distance_km"])
    top = formatted[:MAX_RESULTS]

    logger.info(f"Locator | found={len(top)} | lat={lat} lng={lng} radius={radius_km}km")

    return {
        "phcs": top,
        "total_found": len(top),
        "query": {"lat": lat, "lng": lng, "radius_km": radius_km},
    }