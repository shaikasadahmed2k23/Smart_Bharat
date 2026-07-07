"""Request/response schemas for Smart Bharat API."""
from typing import Optional
from pydantic import BaseModel, Field, field_validator

# add to models.py
from enum import Enum

class ComplaintStatus(str, Enum):
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"

SUPPORTED_LANGUAGES = {"en", "hi", "te"}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    language: str = Field(default="en")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in SUPPORTED_LANGUAGES:
            return "en"
        return v

    @field_validator("message")
    @classmethod
    def strip_message(cls, v: str) -> str:
        return v.strip()


class ChatResponse(BaseModel):
    reply: str
    language: str


class ComplaintCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5, max_length=2000)
    category: str = Field(..., min_length=2, max_length=100)
    location: Optional[str] = Field(default=None, max_length=300)
    language: str = Field(default="en")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in SUPPORTED_LANGUAGES:
            return "en"
        return v


class ComplaintOut(BaseModel):
    id: int
    title: str
    description: str
    category: str
    location: Optional[str]
    status: str
    language: str
    created_at: str


class ComplaintStatusUpdate(BaseModel):
    status: ComplaintStatus




class ServiceQuery(BaseModel):
    need: str = Field(..., min_length=2, max_length=300)
    language: str = Field(default="en")


class DocumentQuery(BaseModel):
    service_name: str = Field(..., min_length=2, max_length=200)
    language: str = Field(default="en")
