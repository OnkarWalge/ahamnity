from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Ahamnity backend starting up...")
    yield
    logger.info("Ahamnity backend shutting down...")


app = FastAPI(
    title="Ahamnity Health Triage API",
    description="Voice-first multilingual AI health triage for rural India",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://ahamnity-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from agents.voice_agent import router as voice_router
from agents.triage_agent import router as triage_router
from agents.locator_agent import router as locator_router
from agents.scheme_agent import router as scheme_router
from agents.red_flag import router as red_flag_router
from agents.cases_router import router as cases_router
from agents.pipeline_agent import router as pipeline_router
from tts.tts_engine import router as tts_router
# from agents.followup_agent import router as followup_router

app.include_router(voice_router,    prefix="/api/voice",    tags=["Voice"])
app.include_router(triage_router,   prefix="/api/triage",   tags=["Triage"])
app.include_router(tts_router,      prefix="/api/tts",      tags=["TTS"])
app.include_router(locator_router,  prefix="/api/locator",  tags=["Locator"])
app.include_router(scheme_router,   prefix="/api/schemes",  tags=["Schemes"])
app.include_router(red_flag_router, prefix="/api/redflag",  tags=["Red Flag"])
app.include_router(cases_router,    prefix="/api/cases",    tags=["Cases"])
app.include_router(pipeline_router, prefix="/api/pipeline", tags=["Pipeline"])
# app.include_router(followup_router, prefix="/api/followup", tags=["Follow-up"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agents": {
            "voice":    "active",
            "triage":   "active",
            "tts":      "active",
            "locator":  "active",
            "schemes":  "active",
            "red_flag": "active",
            "cases":    "active",
            "pipeline": "active",
            "followup": "pending",
        },
    }