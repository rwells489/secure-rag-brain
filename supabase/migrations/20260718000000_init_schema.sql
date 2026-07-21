-- Enable extension for vector embeddings
create extension if not exists vector;

-- Core document registry
create table user_documents (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) not null,
  title text not null,
  content text not null,
  storage_path text unique,
  classification_status text default 'pending', -- pending, approved, quarantined
  pii_detected boolean default false,
  detected_pii_types jsonb default '[]',
  embedding vector(1536),
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Optimize similarity searches using HNSW
create index on user_documents
using hnsw (embedding vector_cosine_ops);

-- Partial indexes for tenant-scoped queries (performance at scale)
create index on user_documents (user_id) where classification_status = 'approved';
create index on user_documents (user_id) where classification_status = 'quarantined';
create index on user_documents (created_at desc);