"""
Request and response schemas for Smart Bharat API.

Pydantic models for input validation and output serialization.
Includes complaint status enum, language support validation, and API contract definitions.
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ComplaintStatus(str, Enum):
    """Valid complaint status values."""
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"


SUPPORTED_LANGUAGES = {"en", "hi", "te"}


class ChatRequest(BaseModel):
    """
    Request schema for the chat endpoint.
    
    Attributes:
        message: Citizen query (1-1000 chars).
        language: Response language code (default "en").
    """
    message: str = Field(..., min_length=1, max_length=1000)
    language: str = Field(default="en")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Fall back to English for unsupported language codes."""
        if v not in SUPPORTED_LANGUAGES:
            return "en"
        return v

    @field_validator("message")
    @classmethod
    def strip_message(cls, v: str) -> str:
        """Strip whitespace from message."""
        return v.strip()


class ChatResponse(BaseModel):
    """
    Response schema for the chat endpoint.
    
    Attributes:
        reply: AI-generated text response.
        language: Echo of requested language.
    """
    reply: str
    language: str


class ComplaintCreate(BaseModel):
    """
    Request schema for filing a new complaint.
    
    Attributes:
        title: Short complaint title (3-200 chars).
        description: Detailed description (5-2000 chars).
        category: Service category (e.g., 'road', 'water').
        location: Optional location string (max 300 chars).
        language: Complaint language (default "en").
    """
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5, max_length=2000)
    category: str = Field(..., min_length=2, max_length=100)
    location: Optional[str] = Field(default=None, max_length=300)
    language: str = Field(default="en")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Fall back to English for unsupported language codes."""
        if v not in SUPPORTED_LANGUAGES:
            return "en"
        return v


class ComplaintOut(BaseModel):
    """
    Response schema for complaint records.
    
    Attributes:
        id: Database record ID.
        title: Complaint title.
        description: Complaint description.
        category: Service category.
        location: Optional location string.
        status: Current complaint status (from ComplaintStatus enum).
        language: Complaint language.
        created_at: ISO timestamp of creation.
    """
    id: int
    title: str
    description: str
    category: str
    location: Optional[str]
    status: str
    language: str
    created_at: str


class ComplaintStatusUpdate(BaseModel):
    """
    Request schema for updating a complaint's status.
    
    Attributes:
        status: New status value (must be valid ComplaintStatus enum member).
    """
    status: ComplaintStatus


class ServiceQuery(BaseModel):
    """
    Request schema for service recommendation endpoint.
    
    Attributes:
        need: User's stated need (2-300 chars).
        language: Response language (default "en").
    """
    need: str = Field(..., min_length=2, max_length=300)
    language: str = Field(default="en")


class DocumentQuery(BaseModel):
    """
    Request schema for document requirements endpoint.
    
    Attributes:
        service_name: Government service name to look up (2-200 chars).
        language: Response language (default "en").
    """
    service_name: str = Field(..., min_length=2, max_length=200)
    language: str = Field(default="en")

