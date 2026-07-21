-- Development seed data for local Supabase
-- Run: supabase db reset (applies migrations + this seed)

-- Test user (password: testpassword123)
-- This user is created via Supabase Auth, not SQL
-- Use Supabase dashboard or CLI to create: supabase auth sign-up -e test@example.com -p testpassword123

-- Sample documents for testing (inserted via Lambda/Edge Function)
-- These demonstrate the classification_status enum and RLS

-- Note: In production, documents are inserted by the ingestion pipeline
-- with user_id set from validated JWT

-- Example approved document (visible to user)
INSERT INTO user_documents (id, user_id, title, content, storage_path, classification_status, pii_detected, detected_pii_types, embedding)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  '00000000-0000-0000-0000-000000000001',  -- Replace with actual user ID
  'Project Alpha - Q3 Roadmap',
  'Project Alpha Q3 roadmap includes feature freeze on Sept 15, beta release Oct 1, GA Nov 15. Key milestones: API v2 migration, dashboard redesign, mobile SDK 2.0.',
  'documents/00000000-0000-0000-0000-000000000001.txt',
  'approved',
  false,
  '[]',
  NULL
);

-- Example quarantined document (visible to user but flagged)
INSERT INTO user_documents (id, user_id, title, content, storage_path, classification_status, pii_detected, detected_pii_types, pii_matches)
VALUES (
  '00000000-0000-0000-0000-000000000002',
  '00000000-0000-0000-0000-000000000001',  -- Replace with actual user ID
  'Employee Onboarding Checklist',
  'Welcome John Doe! Your SSN is 123-45-6789. Email: john.doe@company.com. Please complete I-9 by Friday.',
  'documents/00000000-0000-0000-0000-000000000002.txt',
  'quarantined',
  true,
  '["SSN", "Email"]',
  '{"SSN": ["123-45-6789"], "Email": ["john.doe@company.com"]}'
);

-- Example pending document (just uploaded, awaiting triage)
INSERT INTO user_documents (id, user_id, title, content, storage_path, classification_status, pii_detected)
VALUES (
  '00000000-0000-0000-0000-000000000003',
  '00000000-0000-0000-0000-000000000001',  -- Replace with actual user ID
  'API Integration Notes',
  'Need to integrate with Stripe API for payments. Webhook endpoint: /webhooks/stripe. Test mode keys should be used.',
  'documents/00000000-0000-0000-0000-000000000003.txt',
  'pending',
  false
);

-- Index for faster queries on classification status
-- (Already created in migration: partial indexes on user_id where classification_status = 'approved'/'quarantined')