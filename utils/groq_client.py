from __future__ import annotations

import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

_client: Groq | None = None


def get_groq_client() -> Groq:
    """Returns a singleton Groq client. Call this inside agent nodes."""

    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY is not set in environment.")
        _client = Groq(api_key=api_key)
    return _client


def call_groq(
    system_prompt: str, user_prompt: str, model: str = "llama3-70b-8192"
) -> str:
    """Deterministic Groq chat completion wrapper (temperature=0)."""

    client = get_groq_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        max_tokens=2048,
    )
    return response.choices[0].message.content
