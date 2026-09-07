"""
Apply Supabase migration via the management API.
Run with: .venv\Scripts\python.exe scratch\apply_migration.py
"""
from dotenv import load_dotenv
load_dotenv('backend/.env')
import os, httpx

service_key = os.getenv('SUPABASE_KEY')
project_ref = 'ryfubtdfsqbiawjrasuu'

statements = [
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS job_title TEXT",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED'",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS verification_score INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS verification_details JSONB",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMPTZ",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS normalized_email TEXT",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS normalized_phone TEXT",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS normalized_company TEXT",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS is_candidate BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS source_record_id TEXT",
    """CREATE TABLE IF NOT EXISTS lead_imports (
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
    )""",
    "CREATE INDEX IF NOT EXISTS idx_leads_verification_status ON leads(verification_status)",
    "CREATE INDEX IF NOT EXISTS idx_leads_verification_score ON leads(verification_score)",
    "CREATE INDEX IF NOT EXISTS idx_leads_country ON leads(country)",
    "CREATE INDEX IF NOT EXISTS idx_leads_industry ON leads(industry)",
    "CREATE INDEX IF NOT EXISTS idx_leads_job_title ON leads(job_title)",
    "CREATE INDEX IF NOT EXISTS idx_leads_is_candidate ON leads(is_candidate)",
    "CREATE INDEX IF NOT EXISTS idx_leads_normalized_email ON leads(normalized_email)",
    "CREATE INDEX IF NOT EXISTS idx_leads_normalized_company ON leads(normalized_company)",
    "ALTER TABLE lead_imports ENABLE ROW LEVEL SECURITY",
    "DROP POLICY IF EXISTS \"Lead imports viewable by authenticated users\" ON lead_imports",
    "CREATE POLICY \"Lead imports viewable by authenticated users\" ON lead_imports FOR SELECT TO authenticated USING (true)",
    "DROP POLICY IF EXISTS \"Lead imports insertable by authenticated users\" ON lead_imports",
    "CREATE POLICY \"Lead imports insertable by authenticated users\" ON lead_imports FOR INSERT TO authenticated WITH CHECK (true)",
]

url = f"https://api.supabase.com/v1/projects/{project_ref}/database/query"
headers = {
    "Authorization": f"Bearer {service_key}",
    "Content-Type": "application/json"
}

passed = 0
failed = 0
for stmt in statements:
    try:
        resp = httpx.post(url, headers=headers, json={"query": stmt}, timeout=15)
        if resp.status_code in [200, 201]:
            print(f"OK: {stmt[:80]}...")
            passed += 1
        else:
            print(f"ERR ({resp.status_code}): {stmt[:60]} -> {resp.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"EXCEPTION for stmt '{stmt[:60]}': {e}")
        failed += 1

print(f"\nMigration done: {passed} passed, {failed} failed")
