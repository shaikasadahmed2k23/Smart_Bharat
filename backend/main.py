
"""
Smart Bharat - AI-Powered Civic Companion FastAPI Backend.

Provides endpoints for:
- Chat with AI civic assistant (ask_gemini)
- Service recommendations (civic_data)
- Document lookup (civic_data)
- Complaint creation and tracking (database)
"""

# Standard library
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

# Third-party
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

# Local
from database import get_conn, init_db, get_complaint_by_id
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
from middleware import rate_limit_middleware

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart_bharat")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    
    Initializes the database on startup and logs readiness.
    """
    init_db()
    logger.info("Smart Bharat backend started, database ready.")
    yield


app = FastAPI(
    title="Smart Bharat - AI Civic Companion API",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware stack: gzip compression, CORS, custom rate-limiting + security headers
app.add_middleware(GZipMiddleware, minimum_size=1000)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)

# app.add_middleware(rate_limit_middleware)  # type: ignore
app.middleware("http")(rate_limit_middleware)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Basic liveness probe for health checks and monitoring."""
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler: log unhandled errors and return generic 500.
    
    Prevents raw exception traces from leaking to clients.
    """
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."}
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    """
    Ask the GenAI civic companion a question.
    
    Args:
        payload: ChatRequest with message and optional language.
    
    Returns:
        ChatResponse with AI-generated reply and language echo.
    
    Raises:
        HTTPException: 503 if Gemini API is unavailable; 500 on other errors.
    """
    try:
        # Run blocking Gemini call in thread pool
        reply = await asyncio.to_thread(ask_gemini, payload.message, payload.language)
        return ChatResponse(reply=reply, language=payload.language)
    except RuntimeError as exc:
        logger.error("Gemini error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="AI assistant is temporarily unavailable."
        )
    except Exception:
        logger.exception("Unexpected chat error")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong. Please try again."
        )


@app.post("/api/services/recommend")
async def recommend_services(payload: ServiceQuery) -> dict:
    """
    Recommend relevant government services based on a stated need.
    
    Args:
        payload: ServiceQuery with user's need statement and language.
    
    Returns:
        Dictionary with "results" list and optional "message" if no match found.
    """
    results = search_services(payload.need)
    if not results:
        return {
            "results": [],
            "message": "No exact match found. Try describing your need differently."
        }
    return {"results": results}


@app.post("/api/documents/requirements")
async def document_requirements(payload: DocumentQuery) -> dict:
    """
    Return the documents required for a given public service.
    
    Args:
        payload: DocumentQuery with service name and language.
    
    Returns:
        Dictionary with service name, required documents list, and portal URL.
    
    Raises:
        HTTPException: 404 if service not found in catalog.
    """
    service = find_service_by_name(payload.service_name)
    if not service:
        raise HTTPException(
            status_code=404,
            detail="Service not found in our catalog yet."
        )
    return {
        "service": service["name"],
        "documents": service["documents"],
        "portal": service["portal"],
    }


@app.post("/api/complaints", response_model=ComplaintOut, status_code=201)
async def create_complaint(payload: ComplaintCreate) -> ComplaintOut:
    """
    File a new civic complaint.
    
    Args:
        payload: ComplaintCreate with title, description, category, location, language.
    
    Returns:
        ComplaintOut with newly created complaint including ID and status.
    """
    def _create():
        with get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO complaints (title, description, category, location, language)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    payload.title,
                    payload.description,
                    payload.category,
                    payload.location,
                    payload.language
                ),
            )
            conn.commit()
            return get_complaint_by_id(conn, cursor.lastrowid)
    
    result = await asyncio.to_thread(_create)
    return result  # type: ignore


@app.get("/api/complaints", response_model=list[ComplaintOut])
async def list_complaints(limit: int = 50) -> list[ComplaintOut]:
    """
    List recent complaints (most recent first), capped by limit.
    
    Args:
        limit: Maximum number of complaints to return (default 50).
    
    Returns:
        List of ComplaintOut records, newest first.
    """
    def _list():
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM complaints ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
    
    result = await asyncio.to_thread(_list)
    return result  # type: ignore


@app.get("/api/complaints/{complaint_id}", response_model=ComplaintOut)
async def get_complaint(complaint_id: int = Path(..., ge=1)) -> ComplaintOut:
    """
    Track a specific complaint by ID.
    
    Args:
        complaint_id: Integer complaint ID (>= 1).
    
    Returns:
        ComplaintOut record for the given ID.
    
    Raises:
        HTTPException: 404 if complaint not found.
    """
    def _get():
        with get_conn() as conn:
            return get_complaint_by_id(conn, complaint_id)
    
    result = await asyncio.to_thread(_get)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    return result  # type: ignore


@app.patch("/api/complaints/{complaint_id}", response_model=ComplaintOut)
async def update_complaint_status(
    payload: ComplaintStatusUpdate,
    complaint_id: int = Path(..., ge=1)
) -> ComplaintOut:
    """
    Update a complaint's status (submitted / in_review / resolved / rejected).
    
    Args:
        payload: ComplaintStatusUpdate with new status enum value.
        complaint_id: Integer complaint ID (>= 1).
    
    Returns:
        ComplaintOut with updated status.
    
    Raises:
        HTTPException: 404 if complaint not found.
    """
    def _update():
        with get_conn() as conn:
            existing = get_complaint_by_id(conn, complaint_id)
            if not existing:
                return None
            conn.execute(
                "UPDATE complaints SET status = ? WHERE id = ?",
                (payload.status, complaint_id)
            )
            conn.commit()
            return get_complaint_by_id(conn, complaint_id)
    
    result = await asyncio.to_thread(_update)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    return result  # type: ignore
