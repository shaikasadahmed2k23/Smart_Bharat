


"""
Smart Bharat - AI-Powered Civic Companion
FastAPI backend: chat assistant, service recommender, document
requirement lookup, and complaint tracking.
"""



import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware

from database import get_conn, init_db
from models import (
    ChatRequest,
    ChatResponse,
    ComplaintCreate,
    ComplaintOut,
    ComplaintStatusUpdate,
    ServiceQuery,
    DocumentQuery,
)
from civic_data import search_services, find_service_by_name
from gemini_client import ask_gemini
from fastapi.responses import JSONResponse
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart_bharat")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Smart Bharat backend started, database ready.")
    yield


app = FastAPI(
    title="Smart Bharat - AI Civic Companion API",
    version="1.0.0",
    lifespan=lifespan,
)

from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)

import time
from collections import defaultdict
from fastapi import Request

_request_log: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT = 30          # requests
RATE_WINDOW = 60         # seconds


@app.middleware("http")
async def security_and_rate_limit(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    _request_log[client_ip] = [t for t in _request_log[client_ip] if now - t < RATE_WINDOW]
    if len(_request_log[client_ip]) >= RATE_LIMIT:
        return JSONResponse(status_code=429, content={"detail": "Too many requests. Please slow down."})
    _request_log[client_ip].append(now)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
    return response


@app.get("/health")
def health_check():
    """Basic liveness probe."""
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    """Ask the GenAI civic companion a question."""
    try:
        reply = ask_gemini(payload.message, payload.language)
        return ChatResponse(reply=reply, language=payload.language)
    except RuntimeError as exc:
        logger.error("Gemini error: %s", exc)
        raise HTTPException(status_code=503, detail="AI assistant is temporarily unavailable.")
    except Exception:
        logger.exception("Unexpected chat error")
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again.")


@app.post("/api/services/recommend")
def recommend_services(payload: ServiceQuery):
    """Recommend relevant government services based on a stated need."""
    results = search_services(payload.need)
    if not results:
        return {"results": [], "message": "No exact match found. Try describing your need differently."}
    return {"results": results}


@app.post("/api/documents/requirements")
def document_requirements(payload: DocumentQuery):
    """Return the documents required for a given public service."""
    service = find_service_by_name(payload.service_name)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found in our catalog yet.")
    return {
        "service": service["name"],
        "documents": service["documents"],
        "portal": service["portal"],
    }


@app.post("/api/complaints", response_model=ComplaintOut, status_code=201)
def create_complaint(payload: ComplaintCreate):
    """File a new civic complaint."""
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO complaints (title, description, category, location, language)
            VALUES (?, ?, ?, ?, ?)
            """,
            (payload.title, payload.description, payload.category, payload.location, payload.language),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM complaints WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return dict(row)


@app.get("/api/complaints", response_model=list[ComplaintOut])
def list_complaints(limit: int = 50):
    """List recent complaints, capped by the provided limit."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM complaints ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/complaints/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: int = Path(..., ge=1)):
    """Track a specific complaint by ID."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    return dict(row)


@app.patch("/api/complaints/{complaint_id}", response_model=ComplaintOut)
def update_complaint_status(payload: ComplaintStatusUpdate, complaint_id: int = Path(..., ge=1)):
    """Update a complaint's status (submitted / in_review / resolved / rejected)."""
    with get_conn() as conn:
        existing = conn.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Complaint not found.")
        conn.execute(
            "UPDATE complaints SET status = ? WHERE id = ?", (payload.status, complaint_id)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
    return dict(row)
