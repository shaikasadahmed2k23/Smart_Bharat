"""
Curated catalog of common Indian public services and their document requirements.

Keeping this as structured data (instead of relying purely on the LLM)
makes recommendations deterministic, testable, and fast. Search and lookup
functions are cached with LRU since PUBLIC_SERVICES is static.
"""
import re
from functools import lru_cache
from difflib import SequenceMatcher
from typing import Optional

PUBLIC_SERVICES = [

    {
        "name": "Aadhaar Card",
        "keywords": ["identity", "id proof", "aadhaar", "uid", "biometric"],
        "description": "Unique identity number issued by UIDAI, required for most government schemes.",
        "portal": "https://uidai.gov.in",
        "documents": ["Proof of Identity (PAN/Passport/Voter ID)", "Proof of Address", "Proof of Date of Birth"],
    },
    {
        "name": "PAN Card",
        "keywords": ["tax", "pan", "income tax", "bank account"],
        "description": "Permanent Account Number for tax filing and financial transactions.",
        "portal": "https://www.incometax.gov.in",
        "documents": ["Proof of Identity", "Proof of Address", "Passport size photo"],
    },
    {
        "name": "Ration Card",
        "keywords": ["food", "ration", "subsidy", "pds"],
        "description": "Enables subsidized food grains through the Public Distribution System.",
        "portal": "https://nfsa.gov.in",
        "documents": ["Aadhaar Card", "Address Proof", "Income Certificate", "Family photo"],
    },
    {
        "name": "Income Certificate",
        "keywords": ["income", "certificate", "scholarship", "caste"],
        "description": "Official proof of annual family income, needed for scholarships/reservations.",
        "portal": "https://services.india.gov.in",
        "documents": ["Aadhaar Card", "Salary slips / self-declaration", "Address proof"],
    },
    {
        "name": "Passport",
        "keywords": ["passport", "travel", "visa"],
        "description": "Travel document issued by the Ministry of External Affairs.",
        "portal": "https://www.passportindia.gov.in",
        "documents": ["Aadhaar Card", "Proof of Address", "Proof of Date of Birth"],
    },
    {
        "name": "Voter ID (EPIC)",
        "keywords": ["voter", "election", "epic", "vote"],
        "description": "Enables voting in elections, issued by the Election Commission of India.",
        "portal": "https://voters.eci.gov.in",
        "documents": ["Age proof (18+)", "Address proof", "Passport size photo"],
    },
    {
        "name": "Ayushman Bharat Health Card",
        "keywords": ["health", "medical", "insurance", "hospital", "ayushman"],
        "description": "Free health insurance cover up to ₹5 lakh per family per year.",
        "portal": "https://beneficiary.nha.gov.in",
        "documents": ["Aadhaar Card", "Ration Card", "Income Certificate"],
    },
    {
        "name": "PM Kisan Samman Nidhi",
        "keywords": ["farmer", "agriculture", "kisan", "crop"],
        "description": "Income support of ₹6000/year for eligible farmer families.",
        "portal": "https://pmkisan.gov.in",
        "documents": ["Aadhaar Card", "Land ownership papers", "Bank account details"],
    },
]


@lru_cache(maxsize=128)
def search_services(query: str, top_k: int = 3) -> list[dict]:
    """
    Search the curated service catalog using keyword overlap ranking.
    
    Cached with LRU since PUBLIC_SERVICES is static. Handles variations
    and partial matches to improve recall over exact-match lookup.
    
    Args:
        query: User search query string (e.g., "I need passport to travel").
        top_k: Maximum number of results to return (default 3).
    
    Returns:
        List of up to top_k service dictionaries, sorted by relevance score.
    """
    query_lower = query.lower()
    scored = []
    for service in PUBLIC_SERVICES:
        score = sum(1 for kw in service["keywords"] if kw in query_lower)
        if service["name"].lower() in query_lower:
            score += 2
        if score > 0:
            scored.append((score, service))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:top_k]]


def _normalize(text: str) -> str:
    """
    Normalize text for fuzzy matching.
    
    Converts to lowercase, removes punctuation, and collapses whitespace
    to enable typo-tolerant service name lookups.
    
    Args:
        text: Raw input text.
    
    Returns:
        Normalized text string.
    """
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return re.sub(r"\s+", " ", text)


@lru_cache(maxsize=128)
def find_service_by_name(name: str) -> Optional[dict]:
    """
    Fuzzy-match a user-typed service name against the catalog.
    
    Handles typos (e.g., 'aadhar' -> 'Aadhaar Card') via SequenceMatcher
    similarity scoring. Returns exact/substring match if found; otherwise
    returns best match if score >= 0.6. Cached with LRU for efficiency.
    
    Args:
        name: Service name from user input (possibly misspelled).
    
    Returns:
        Service dictionary if found (exact or fuzzy match), None otherwise.
    """
    query = _normalize(name)
    best_match, best_score = None, 0.0

    for service in PUBLIC_SERVICES:
        service_norm = _normalize(service["name"])
        if service_norm == query or service_norm in query or query in service_norm:
            return service
        score = SequenceMatcher(None, query, service_norm).ratio()
        if score > best_score:
            best_score, best_match = score, service

    return best_match if best_score >= 0.6 else None