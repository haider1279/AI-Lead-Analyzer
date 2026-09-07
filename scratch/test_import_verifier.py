import io
import json
import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backend.app.services.lead_importer import LeadDatasetImporter
from backend.app.services.lead_verifier import LeadVerificationEngine


sample_csv = """Company,Contact Name,Job Title,Email,Website,Country,Industry,Budget
Acme Cloud Corp,Alice Smith,CTO,alice@acme.com,https://google.com,United States,Cloud Computing,45000
Apex FinTech Ltd,Bob Jones,VP Engineering,bob@apexfin.co.uk,https://github.com,United Kingdom,Financial Services,30000
Duplicate Acme,Alice Smith,CTO,alice@acme.com,https://google.com,United States,Cloud Computing,45000
Broken Corp,,,invalid_email_no_at,http://127.0.0.1,France,Consulting,10000
"""

# 1. Test preview
preview = LeadDatasetImporter.generate_preview(sample_csv.encode("utf-8"), "test_leads.csv")
print("=== 1. PREVIEW GENERATED ===")
print("Headers:", preview["detected_headers"])
print("Suggested Mappings:", preview["suggested_mappings"])
print("Preview rows count:", len(preview["preview_rows"]))

# 2. Test full import with deduplication and verification
result = LeadDatasetImporter.process_import(
    file_bytes=sample_csv.encode("utf-8"),
    filename="test_leads.csv",
    column_mapping=preview["suggested_mappings"],
    existing_leads=[],
    auto_verify=True,
    source_name="Synthetic Test CSV"
)

print("\n=== 2. IMPORT RESULT STATS ===")
print("Total rows:", result["total_rows"])
print("Valid rows:", result["valid_rows"])
print("Duplicates:", result["duplicate_rows"])
print("Verified rows:", result["verified_rows"])
print("Unverified rows:", result["unverified_rows"])
print("Invalid rows:", result["invalid_rows"])

for lead in result["imported_leads"]:
    cname = lead.get("company_name")
    vstatus = lead.get("verification_status")
    vscore = lead.get("verification_score")
    print(f"Lead: {cname} | Status: {vstatus} | Score: {vscore}%")
