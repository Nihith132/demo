from __future__ import annotations

import json
import os
from functools import lru_cache

import firebase_admin
from firebase_admin import auth, credentials


@lru_cache(maxsize=1)
def _init_firebase() -> None:
    if firebase_admin._apps:
        return

    svc_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    svc_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    project_id = os.getenv("FIREBASE_PROJECT_ID")

    # Preferred: file path (works well locally; avoids multi-line env JSON issues)
    if svc_path:
        cred = credentials.Certificate(svc_path)
        firebase_admin.initialize_app(cred)
        return

    # Alternative: one-line JSON in env
    if svc_json:
        info = json.loads(svc_json)
        cred = credentials.Certificate(info)
        firebase_admin.initialize_app(cred)
        return

    # Fallback: attempt application default credentials (works on some deployments)
    if project_id:
        firebase_admin.initialize_app(options={"projectId": project_id})
        return

    raise RuntimeError(
        "Firebase is not configured. Set FIREBASE_SERVICE_ACCOUNT_PATH (recommended) or FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_PROJECT_ID."
    )


def verify_firebase_id_token(id_token: str) -> dict:
    _init_firebase()
    try:
        return auth.verify_id_token(id_token)
    except Exception as e:
        # Don't log tokens. Just surface root cause in server logs.
        print(f"firebase_verify_id_token_failed: {type(e).__name__}: {e}")
        raise
