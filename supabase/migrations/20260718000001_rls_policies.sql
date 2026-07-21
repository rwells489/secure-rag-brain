-- Enable Row Level Security
alter table user_documents enable row level security;

-- Policy: Users can only see their own approved documents
create policy "users_select_own_approved"
on user_documents for select
using (
  auth.uid() = user_id
  and classification_status = 'approved'
);

-- Policy: Users can see their own quarantined documents (for review)
create policy "users_select_own_quarantined"
on user_documents for select
using (
  auth.uid() = user_id
  and classification_status = 'quarantined'
);

-- Policy: Users can insert their own documents (pending classification)
create policy "users_insert_own"
on user_documents for insert
with check (auth.uid() = user_id);

-- Policy: Users cannot update classification_status directly (server-only)
-- Only the lambda/edge function (service role) can update status
create policy "service_role_full_access"
on user_documents for all
using (auth.role() = 'service_role');

-- Optional: Admin policy for auditing
create policy "admin_select_all"
on user_documents for select
using (
  exists (
    select 1 from auth.users
    where id = auth.uid()
    and raw_user_meta_data->>'role' = 'admin'
  )
);