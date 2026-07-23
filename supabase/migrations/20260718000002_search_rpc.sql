-- Add pgvector search RPC function for tenant-scoped semantic search
-- This function is called by the Search Lambda / Edge Function

create or replace function search_user_documents(
  query_embedding vector(1536),
  match_count int default 10,
  filter_user_id uuid
)
returns table (
  id uuid,
  title text,
  content text,
  similarity float
)
language sql
security definer
set search_path = public
as $$
  select
    d.id,
    d.title,
    d.content,
    1 - (d.embedding <=> query_embedding) as similarity
  from user_documents d
  where d.user_id = filter_user_id
    and d.classification_status = 'approved'
    and d.embedding is not null
  order by d.embedding <=> query_embedding
  limit match_count;
$$;

-- Grant execute to service role (Lambda/Edge Functions) and authenticated users
grant execute on function search_user_documents(vector(1536), int, uuid) to service_role;
grant execute on function search_user_documents(vector(1536), int, uuid) to authenticated;