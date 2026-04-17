"""
ESI vector store utilities.
- Chunk ESI protocol text
- Embed with sentence-transformers/all-MiniLM-L6-v2
- Store/search in pgvector (Supabase Postgres)
"""

from __future__ import annotations

import os

from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.orm import Session

# Load embedding model once at module init
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))

try:
    _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
except Exception as e:
    print(f"Warning: Failed to load embedding model {EMBEDDING_MODEL_NAME}: {e}")
    _embedding_model = None


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Embed a batch of texts using the Hugging Face sentence-transformers model.
    Returns list of embedding vectors (list of floats).
    """
    if _embedding_model is None:
        raise RuntimeError("Embedding model not loaded. Check EMBEDDING_MODEL env var.")
    
    embeddings = _embedding_model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """
    Simple chunking strategy: split by sentence + overlap.
    For ESI protocols, you might want more sophisticated chunking.
    """
    sentences = text.split(". ")
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # Start new chunk with overlap
            current_chunk = sentence
        else:
            current_chunk += ". " + sentence if current_chunk else sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def ingest_esi_protocol(
    db: Session,
    source_text: str,
    source_name: str = "ESI Protocol Overview",
    version: str = "1.0",
) -> dict:
    """
    Ingest ESI protocol text:
    1. Split into chunks
    2. Embed each chunk
    3. Store in esi_documents + esi_chunks table
    
    Returns dict with ingestion stats.
    """
    from models.esi_models import ESIDocument, ESIChunk
    
    # Create document record
    doc = ESIDocument(source=source_name, version=version)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # Chunk the text
    chunks = chunk_text(source_text)
    chunk_embeddings = get_embeddings(chunks)
    
    # Parse ESI structure to extract metadata per chunk
    # This is simplified; you might enhance it based on ESI section markers
    chunk_records = []
    for idx, (chunk_text, embedding) in enumerate(zip(chunks, chunk_embeddings)):
        # Simple heuristic: detect decision point from text
        title = None
        metadata = {}
        
        if "Decision Point A" in chunk_text or "ESI Level 1" in chunk_text:
            title = "Decision Point A: ESI 1 (Resuscitation)"
            metadata = {"esi_level": 1, "decision_point": "A"}
        elif "Decision Point B" in chunk_text or "ESI Level 2" in chunk_text:
            title = "Decision Point B: ESI 2 (Emergent)"
            metadata = {"esi_level": 2, "decision_point": "B"}
        elif "Decision Point C" in chunk_text or "Resource Assessment" in chunk_text:
            title = "Decision Point C: Resource Assessment"
            metadata = {"esi_level": None, "decision_point": "C"}
        elif "Decision Point D" in chunk_text or "ESI Level 3" in chunk_text:
            title = "Decision Point D: ESI 3 (Urgent)"
            metadata = {"esi_level": 3, "decision_point": "D"}
        elif "Decision Point E" in chunk_text or "ESI Level 4" in chunk_text:
            title = "Decision Point E: ESI 4 (Less Urgent)"
            metadata = {"esi_level": 4, "decision_point": "E"}
        elif "Decision Point F" in chunk_text or "ESI Level 5" in chunk_text:
            title = "Decision Point F: ESI 5 (Non-Urgent)"
            metadata = {"esi_level": 5, "decision_point": "F"}
        
        # Convert embedding to PostgreSQL vector format
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        chunk_obj = ESIChunk(
            document_id=doc.id,
            chunk_index=idx,
            title=title,
            content=chunk_text,
            metadata=metadata,
            embedding=embedding_str,  # SQLAlchemy will handle conversion
        )
        chunk_records.append(chunk_obj)
        db.add(chunk_obj)
    
    db.commit()
    
    return {
        "document_id": str(doc.id),
        "source": source_name,
        "chunks_created": len(chunks),
        "status": "success"
    }


def search_esi_chunks(
    db: Session,
    query_text: str,
    limit: int = 5,
    threshold: float = 0.5,
) -> list[dict]:
    """
    Search ESI chunks by semantic similarity.
    1. Embed query text
    2. Find top-k similar chunks via cosine distance
    
    Returns list of dicts with chunk data + similarity score.
    """
    # Embed the query
    query_embedding = get_embeddings([query_text])[0]
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    
    # Raw SQL: vector similarity search
    # PostgreSQL: embedding <=> query_embedding returns cosine distance
    # 1 - distance = cosine similarity (0 to 1, higher is better)
    sql = text("""
        SELECT
            id,
            title,
            content,
            metadata,
            1 - (embedding <=> :embedding::vector) as similarity
        FROM public.esi_chunks
        WHERE 1 - (embedding <=> :embedding::vector) >= :threshold
        ORDER BY embedding <=> :embedding::vector
        LIMIT :limit
    """)
    
    results = db.execute(
        sql,
        {"embedding": embedding_str, "threshold": threshold, "limit": limit}
    ).fetchall()
    
    return [
        {
            "id": str(r[0]),
            "title": r[1],
            "content": r[2],
            "metadata": r[3],
            "similarity": float(r[4]),
        }
        for r in results
    ]
