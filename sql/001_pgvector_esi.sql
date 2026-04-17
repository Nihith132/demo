-- Enable pgvector + create ESI vector tables (Supabase Postgres)
-- Embedding model: sentence-transformers/all-MiniLM-L6-v2 (384 dims)

-- 1) Extensions
create extension if not exists vector;
create extension if not exists pgcrypto;

-- 2) Source documents table
create table if not exists public.esi_documents (
  id uuid primary key default gen_random_uuid(),
  source text not null,
  version text null,
  created_at timestamptz not null default now()
);

-- 3) Embedded chunks table
create table if not exists public.esi_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.esi_documents(id) on delete cascade,

  chunk_index int not null,
  title text null,
  content text not null,
  metadata jsonb not null default '{}'::jsonb,

  embedding vector(384) not null,

  created_at timestamptz not null default now(),

  constraint esi_chunks_doc_chunk_unique unique (document_id, chunk_index)
);

-- 4) Vector index (cosine distance)
-- NOTE: ivfflat needs ANALYZE after bulk insert for best performance.
create index if not exists esi_chunks_embedding_ivfflat
  on public.esi_chunks
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- 5) Helpful indexes
create index if not exists esi_chunks_document_id_idx on public.esi_chunks(document_id);

-- 6) Example similarity search
-- select id, title, 1 - (embedding <=> '[...]'::vector) as cosine_similarity
-- from public.esi_chunks
-- order by embedding <=> '[...]'::vector
-- limit 8;
