"""
Thin wrapper around the Gemini API for the civic assistant chat.
Centralising the prompt + config here keeps main.py clean and makes
the AI behaviour easy to tune/test independently.
Uses the current `google-genai` SDK (google.generativeai is deprecated).
"""
import os
from google import genai
from google.genai import types

LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "te": "Telugu"}

SYSTEM_INSTRUCTION = """You are Smart Bharat Sahayak, an AI civic companion for Indian citizens.
Your job:
- Explain government services, schemes, and procedures in simple, clear language.
- Help users understand which documents they need for a service.
- Guide users on how to file or track civic complaints (roads, water, electricity, sanitation, etc).
- Always be respectful, concise, and practical. Avoid legal jargon.
- If you are not fully sure about a specific rule, say so honestly and suggest the
  official government portal instead of guessing.
- Never ask for sensitive personal data like Aadhaar number, bank details, or passwords.
Reply ONLY in the language requested, keeping paragraphs short."""

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in environment")
        _client = genai.Client(api_key=api_key)
    return _client


def ask_gemini(message: str, language: str = "en") -> str:
    """Send a citizen query to Gemini and return a plain-text reply."""
    lang_name = LANGUAGE_NAMES.get(language, "English")
    client = _get_client()
    prompt = f"[Respond in {lang_name}]\n\nCitizen query: {message}"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION),
    )
    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError("Empty response from Gemini")
    return text.strip()
