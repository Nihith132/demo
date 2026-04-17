"""
Database models for ESI vector store.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from database import Base


class ESIDocument(Base):
    """Source ESI protocol document."""
    __tablename__ = "esi_documents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    source = Column(String, nullable=False)  # e.g., "ESI Protocol Overview v1"
    version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("ESIChunk", back_populates="document", cascade="all, delete-orphan")


class ESIChunk(Base):
    """Individual embedded chunk of ESI protocol."""
    __tablename__ = "esi_chunks"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey("esi_documents.id", ondelete="CASCADE"), nullable=False)

    chunk_index = Column(Integer, nullable=False)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=False, default=lambda: {})

    # Vector embedding (384 dims for all-MiniLM-L6-v2)
    # Stored as TEXT in SQLAlchemy; PostgreSQL pgvector handles conversion
    embedding = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("ESIDocument", back_populates="chunks")
