from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Language(str, Enum):
    HINDI = "hi"
    MARATHI = "mr"
    ENGLISH = "en"
    BENGALI = "bn"
    TELUGU = "te"
    TAMIL = "ta"


# --- Voice ---
class TranscriptionResponse(BaseModel):
    text: str
    language: str


# --- Triage ---
class TriageRequest(BaseModel):
    symptoms: str
    language: str = "hi"


class TriageResponse(BaseModel):
    risk_level: RiskLevel
    advice: str
    keywords: List[str] = []
    language: str


# --- TTS ---
class TTSRequest(BaseModel):
    text: str
    language: str = "en"


class TTSResponse(BaseModel):
    audio_base64: str
    format: str = "mp3"
    language: str
    voice: str


# --- Pipeline ---
class PipelineResponse(BaseModel):
    transcription: str
    detected_language: str
    risk_level: RiskLevel
    advice: str
    keywords: List[str] = []
    audio_base64: str
    audio_format: str = "mp3"
    timestamp: str


# --- Locator (Step 6 stub) ---
class PHCResult(BaseModel):
    name: str
    address: str
    distance_km: float
    phone: Optional[str] = None
    lat: float
    lng: float


class LocatorRequest(BaseModel):
    lat: float
    lng: float
    radius_km: float = 10.0


class LocatorResponse(BaseModel):
    facilities: List[PHCResult]
    total_found: int


# --- Schemes (Step 7 stub) ---
class SchemeResult(BaseModel):
    scheme_id: str
    name: str
    description: str
    eligibility: str
    benefit: str
    how_to_apply: str


class SchemeRequest(BaseModel):
    symptoms: str
    language: str = "hi"
    risk_level: Optional[RiskLevel] = None


class SchemeResponse(BaseModel):
    schemes: List[SchemeResult]
    total_found: int


# --- Case record (Step 9 Supabase stub) ---
class CaseRecord(BaseModel):
    case_id: Optional[str] = None
    transcription: str
    language: str
    risk_level: RiskLevel
    advice: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    phone: Optional[str] = None
    created_at: Optional[str] = None


# --- Follow-up (Step 11 stub) ---
class FollowUpRequest(BaseModel):
    case_id: str
    phone: str
    language: str = "hi"


class FollowUpResponse(BaseModel):
    scheduled: bool
    case_id: str
    follow_up_time: str
