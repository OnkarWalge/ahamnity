# Stub — implemented in Step 9
# Will use supabase-py for case storage and real-time ASHA alerts
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
logger = logging.getLogger(__name__)

_client: Optional[Client] = None


def get_client() -> Client:
    """
    Returns a cached Supabase client — created once, reused across requests.
    Raises clearly if env vars are missing instead of failing deep inside a call.
    """
    global _client
    if _client is not None:
        return _client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be set in backend/.env. "
            "Get them from Supabase Dashboard → Settings → Data API / API Keys."
        )

    _client = create_client(url, key)
    logger.info("Supabase client initialised")
    return _client


# ---------------------------------------------------------------------------
# supabase-py is synchronous. FastAPI is async. We wrap every call in
# asyncio.to_thread() so a slow DB call never blocks the event loop and
# stalls other patients' requests.
# ---------------------------------------------------------------------------

async def create_case(case_data: dict) -> dict:
    """
    Inserts a new case record. Returns the inserted row (including generated id).
    case_data should match the columns in the `cases` table — see schema.sql.
    """
    client = get_client()

    def _insert():
        result = client.table("cases").insert(case_data).execute()
        return result.data[0] if result.data else None

    row = await asyncio.to_thread(_insert)
    if row:
        logger.info(f"Case saved | id={row['id']} | risk={row.get('risk_level')}")
    return row


async def get_case(case_id: str) -> Optional[dict]:
    """Fetch a single case by id."""
    client = get_client()

    def _fetch():
        result = client.table("cases").select("*").eq("id", case_id).execute()
        return result.data[0] if result.data else None

    return await asyncio.to_thread(_fetch)


async def list_cases(
    limit: int = 50,
    risk_level: Optional[str] = None,
    asha_notified: Optional[bool] = None,
) -> list[dict]:
    """
    Lists recent cases, newest first. Used by the ASHA dashboard later.
    Optional filters: risk_level ('low'|'medium'|'high'), asha_notified (bool).
    """
    client = get_client()

    def _query():
        q = client.table("cases").select("*").order("created_at", desc=True).limit(limit)
        if risk_level:
            q = q.eq("risk_level", risk_level)
        if asha_notified is not None:
            q = q.eq("asha_notified", asha_notified)
        result = q.execute()
        return result.data

    return await asyncio.to_thread(_query)


async def update_case(case_id: str, updates: dict) -> Optional[dict]:
    """Update fields on an existing case (e.g. mark asha_notified=True)."""
    client = get_client()

    def _update():
        result = client.table("cases").update(updates).eq("id", case_id).execute()
        return result.data[0] if result.data else None

    return await asyncio.to_thread(_update)