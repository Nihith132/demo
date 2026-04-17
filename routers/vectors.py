"""
API router for ESI vector store operations.
- POST /api/vectors/esi/ingest - ingest ESI protocol text
- GET /api/vectors/esi/search - search similar chunks
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from routers.auth import get_current_doctor
from models.db_models import Doctor
from utils.esi_vector import ingest_esi_protocol, search_esi_chunks

router = APIRouter()


class ESIIngestRequest(BaseModel):
    text: str = Field(..., description="Full ESI protocol text to ingest")
    source_name: str = Field(default="ESI Protocol", description="Name/source of the protocol")
    version: str = Field(default="1.0", description="Version identifier")


class ESISearchRequest(BaseModel):
    query: str = Field(..., description="Natural language query about ESI protocols")
    limit: int = Field(default=5, ge=1, le=20, description="Max results")
    threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity score")


class ESIChunkResult(BaseModel):
    id: str
    title: str | None
    content: str
    metadata: dict
    similarity: float


class ESIIngestResponse(BaseModel):
    status: str
    document_id: str
    source: str
    chunks_created: int


@router.post("/ingest", response_model=ESIIngestResponse)
def ingest_esi(
    payload: ESIIngestRequest,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """
    Ingest ESI protocol text into vector store.
    Requires doctor authentication.
    """
    try:
        result = ingest_esi_protocol(
            db=db,
            source_text=payload.text,
            source_name=payload.source_name,
            version=payload.version,
        )
        return ESIIngestResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ingestion failed: {str(e)}")


@router.get("/search", response_model=list[ESIChunkResult])
def search_esi(
    query: str,
    limit: int = 5,
    threshold: float = 0.5,
    db: Session = Depends(get_db),
):
    """
    Search ESI protocol chunks by semantic similarity.
    Public endpoint (no auth required for MVP).
    """
    try:
        results = search_esi_chunks(
            db=db,
            query_text=query,
            limit=limit,
            threshold=threshold,
        )
        return [ESIChunkResult(**r) for r in results]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Search failed: {str(e)}")
