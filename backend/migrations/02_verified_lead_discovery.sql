-- ==============================================================================
-- MIGRATION 02: VERIFIED LEAD DISCOVERY & DATASET IMPORT
-- ==============================================================================

-- 1. Extend LEADS table with verification and discovery fields
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS job_title TEXT,
    ADD COLUMN IF NOT EXISTS verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
    ADD COLUMN IF NOT EXISTS verification_score INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS verification_details JSONB,
    ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS normalized_email TEXT,
    ADD COLUMN IF NOT EXISTS normalized_phone TEXT,
    ADD COLUMN IF NOT EXISTS normalized_company TEXT,
    ADD COLUMN IF NOT EXISTS is_candidate BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS source_record_id TEXT;

-- 2. Create LEAD_IMPORTS table to track dataset upload batches
CREATE TABLE IF NOT EXISTS lead_imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name TEXT NOT NULL,
    total_rows INTEGER NOT NULL DEFAULT 0,
    valid_rows INTEGER NOT NULL DEFAULT 0,
    invalid_rows INTEGER NOT NULL DEFAULT 0,
    duplicate_rows INTEGER NOT NULL DEFAULT 0,
    verified_rows INTEGER NOT NULL DEFAULT 0,
    unverified_rows INTEGER NOT NULL DEFAULT 0,
    created_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Create indexes for high-speed discovery and filtering
CREATE INDEX IF NOT EXISTS idx_leads_verification_status ON leads(verification_status);
CREATE INDEX IF NOT EXISTS idx_leads_verification_score ON leads(verification_score);
CREATE INDEX IF NOT EXISTS idx_leads_country ON leads(country);
CREATE INDEX IF NOT EXISTS idx_leads_industry ON leads(industry);
CREATE INDEX IF NOT EXISTS idx_leads_job_title ON leads(job_title);
CREATE INDEX IF NOT EXISTS idx_leads_is_candidate ON leads(is_candidate);
CREATE INDEX IF NOT EXISTS idx_leads_normalized_email ON leads(normalized_email);
CREATE INDEX IF NOT EXISTS idx_leads_normalized_company ON leads(normalized_company);

-- 4. Enable RLS on lead_imports
ALTER TABLE lead_imports ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS  Lead imports viewable by authenticated users ON lead_imports;
CREATE POLICY Lead imports viewable by authenticated users
    ON lead_imports FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS Lead imports insertable by authenticated users ON lead_imports;
CREATE POLICY Lead imports insertable by authenticated users
    ON lead_imports FOR INSERT TO authenticated WITH CHECK (true);
