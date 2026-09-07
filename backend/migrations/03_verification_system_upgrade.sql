-- ==============================================================================
-- MIGRATION 03: VERIFICATION SYSTEM & DATASET IMPORT COLUMNS
-- Execute this script in your Supabase SQL Editor
-- ==============================================================================

-- 1. Extend LEADS table with verification and discovery columns
ALTER TABLE public.leads
    ADD COLUMN IF NOT EXISTS job_title TEXT,
    ADD COLUMN IF NOT EXISTS verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
    ADD COLUMN IF NOT EXISTS verification_score INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS verification_details JSONB,
    ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS is_candidate BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS source_record_id TEXT,
    ADD COLUMN IF NOT EXISTS normalized_email TEXT,
    ADD COLUMN IF NOT EXISTS normalized_phone TEXT,
    ADD COLUMN IF NOT EXISTS normalized_company TEXT;

-- 2. Add verification score range constraint (0-100) safely
DO $$ BEGIN
    ALTER TABLE public.leads 
        ADD CONSTRAINT chk_verification_score CHECK (verification_score >= 0 AND verification_score <= 100);
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 3. Create LEAD_IMPORTS table to track dataset upload batches
CREATE TABLE IF NOT EXISTS public.lead_imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name TEXT NOT NULL,
    total_rows INTEGER NOT NULL DEFAULT 0,
    valid_rows INTEGER NOT NULL DEFAULT 0,
    invalid_rows INTEGER NOT NULL DEFAULT 0,
    duplicate_rows INTEGER NOT NULL DEFAULT 0,
    verified_rows INTEGER NOT NULL DEFAULT 0,
    unverified_rows INTEGER NOT NULL DEFAULT 0,
    accepted_rows INTEGER NOT NULL DEFAULT 0,
    rejected_rows INTEGER NOT NULL DEFAULT 0,
    rejection_threshold INTEGER NOT NULL DEFAULT 70,
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Create high-performance indexes for discovery & verified leads queries
CREATE INDEX IF NOT EXISTS idx_leads_verification_status ON public.leads(verification_status);
CREATE INDEX IF NOT EXISTS idx_leads_verification_score ON public.leads(verification_score);
CREATE INDEX IF NOT EXISTS idx_leads_country ON public.leads(country);
CREATE INDEX IF NOT EXISTS idx_leads_industry ON public.leads(industry);
CREATE INDEX IF NOT EXISTS idx_leads_job_title ON public.leads(job_title);
CREATE INDEX IF NOT EXISTS idx_leads_is_candidate ON public.leads(is_candidate);
CREATE INDEX IF NOT EXISTS idx_leads_normalized_email ON public.leads(normalized_email);
CREATE INDEX IF NOT EXISTS idx_leads_normalized_company ON public.leads(normalized_company);

-- 5. Enable Row Level Security (RLS) on lead_imports
ALTER TABLE public.lead_imports ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Lead imports viewable by authenticated users" ON public.lead_imports;
CREATE POLICY "Lead imports viewable by authenticated users"
    ON public.lead_imports FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Lead imports insertable by authenticated users" ON public.lead_imports;
CREATE POLICY "Lead imports insertable by authenticated users"
    ON public.lead_imports FOR INSERT TO authenticated WITH CHECK (true);
