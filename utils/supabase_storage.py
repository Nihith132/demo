from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from supabase import create_client


@dataclass
class SupabaseUploadResult:
    bucket: str
    object_path: str
    version: str


def _get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(url, key)


def upload_pdf_bytes(*, content: bytes, original_filename: str, content_type: str = "application/pdf") -> SupabaseUploadResult:
    """Upload a PDF to Supabase Storage using the service role key.

    Returns the bucket/object path so we can later mint signed URLs.
    """

    bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "patient-uploads")

    safe_name = (original_filename or "document.pdf").replace(os.sep, "_")
    object_path = f"pdf/{uuid.uuid4().hex}_{safe_name}"

    client = _get_supabase_client()
    storage: Any = client.storage

    resp: Any = storage.from_(bucket).upload(
        path=object_path,
        file=content,
        file_options={"content-type": content_type, "upsert": False},
    )

    if isinstance(resp, dict) and resp.get("error"):
        raise RuntimeError(f"Supabase upload failed: {resp.get('error')}")

    version: str = ""
    try:
        if isinstance(resp, dict) and isinstance(resp.get("data"), dict):
            version = str(resp["data"].get("version") or "")
    except Exception:
        version = ""

    return SupabaseUploadResult(bucket=bucket, object_path=object_path, version=version)


def create_signed_pdf_url(*, bucket: str, object_path: str, expires_in: Optional[int] = None) -> str:
    client = _get_supabase_client()
    storage: Any = client.storage

    if expires_in is None:
        expires_in = int(os.getenv("SUPABASE_SIGNED_URL_EXPIRES_SECONDS", "3600"))

    resp: Any = storage.from_(bucket).create_signed_url(object_path, expires_in)

    if isinstance(resp, dict):
        # Older supabase-py uses shape {"data": {"signedURL": ...}, "error": ...}
        if resp.get("error"):
            raise RuntimeError(f"Supabase signed url failed: {resp.get('error')}")
        data = resp.get("data") or {}
        url = data.get("signedURL") or data.get("signedUrl") or data.get("signed_url")
        if url:
            return url

    url = getattr(resp, "signed_url", None) or getattr(resp, "signedURL", None)
    if url:
        return url

    raise RuntimeError("Failed to generate signed URL")
