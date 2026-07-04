import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from database.supabase_client import create_case, get_case, list_cases, update_case

logger = logging.getLogger(__name__)
router = APIRouter()


class CaseCreateRequest(BaseModel):
    transcript: str
    language: str = "hi"
    risk_level: str  # low | medium | high
    advice: str
    red_flags: list[str] = []
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    district: Optional[str] = None
    patient_phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CaseUpdateRequest(BaseModel):
    asha_notified: Optional[bool] = None
    followup_sent: Optional[bool] = None


@router.post("/")
async def create_case_endpoint(request: CaseCreateRequest):
    """Save a new triage case. Called automatically by the pipeline going forward."""
    if request.risk_level not in ("low", "medium", "high"):
        raise HTTPException(status_code=400, detail="risk_level must be low, medium, or high")

    try:
        row = await create_case(request.model_dump(exclude_none=True))
    except Exception as e:
        logger.error(f"Case creation failed: {e}")
        raise HTTPException(status_code=502, detail=f"Database error: {str(e)}")

    if not row:
        raise HTTPException(status_code=502, detail="Insert returned no data")

    return row


@router.get("/{case_id}")
async def get_case_endpoint(case_id: str):
    """Fetch a single case by id."""
    try:
        row = await get_case(case_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Database error: {str(e)}")

    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    return row


@router.get("/")
async def list_cases_endpoint(
    limit: int = Query(default=50, le=200),
    risk_level: Optional[str] = Query(default=None),
):
    """List recent cases — newest first. Used by ASHA dashboard later."""
    try:
        rows = await list_cases(limit=limit, risk_level=risk_level)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Database error: {str(e)}")

    return {"cases": rows, "total": len(rows)}


@router.patch("/{case_id}")
async def update_case_endpoint(case_id: str, request: CaseUpdateRequest):
    """Update ASHA workflow flags on an existing case."""
    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        row = await update_case(case_id, updates)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Database error: {str(e)}")

    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    return row