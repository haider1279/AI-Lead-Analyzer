import io
import time
import json
import asyncio
import random
from app.services.lead_importer import LeadDatasetImporter
from app.services.lead_verifier import LeadVerificationEngine
from app.db.database import db

DOMAINS = [
    ("google.com", "Google Health"),
    ("microsoft.com", "Microsoft LifeSciences"),
    ("github.com", "GitHub Bio"),
    ("apple.com", "Apple HealthTech"),
    ("amazon.com", "Amazon Pharmacy"),
    ("nih.gov", "National Institute of Health"),
    ("mayoclinic.org", "Mayo Clinic Partner"),
    ("hopkinsmedicine.org", "Johns Hopkins Medicine"),
    ("clevelandclinic.org", "Cleveland Clinic Health"),
    ("pfizer.com", "Pfizer Research"),
    ("novartis.com", "Novartis Pharma"),
    ("roche.com", "Roche Diagnostics"),
    ("astrazeneca.com", "AstraZeneca Labs"),
    ("modernatx.com", "Moderna Therapeutics"),
    ("bayer.com", "Bayer Healthcare")
]

TITLES = [
    "Chief Medical Officer", "Director of Clinical Informatics", "VP Healthcare Operations",
    "Head of Bioinformatics", "Lead Clinical Researcher", "Healthcare IT Director",
    "Medical Science Liaison", "Director of Telehealth"
]

CITIES_COUNTRIES = [
    ("New York", "United States"), ("London", "United Kingdom"), ("Berlin", "Germany"),
    ("Toronto", "Canada"), ("Zurich", "Switzerland"), ("Singapore", "Singapore"),
    ("Boston", "United States"), ("San Francisco", "United States")
]

def generate_1000_row_healthcare_csv() -> Tuple[str, bytes]:
    lines = ["Company Name,Contact Name,Job Title,Email Address,Website,Country,Industry,Est Budget,Description"]
    
    # Generate 950 unique leads across major healthcare and clinical domains
    for i in range(1, 951):
        domain, company_prefix = DOMAINS[i % len(DOMAINS)]
        company_name = f"{company_prefix} Group {i}"
        first_names = ["Sarah", "James", "Elena", "Marcus", "Emily", "David", "Aisha", "Michael"]
        last_names = ["Vance", "Mercer", "Chen", "Patel", "Muller", "O'Connor", "Kim", "Taylor"]
        contact_name = f"Dr. {first_names[i % len(first_names)]} {last_names[(i * 3) % len(last_names)]}"
        job_title = TITLES[i % len(TITLES)]
        email = f"lead_{i}@{domain}"
        website = f"https://{domain}"
        _, country = CITIES_COUNTRIES[i % len(CITIES_COUNTRIES)]
        industry = "Healthcare & Life Sciences"
        budget = 25000 + (i % 20) * 5000
        desc = f"Electronic health record modernization and clinical workflow integration for unit {i}."
        
        lines.append(f'"{company_name}","{contact_name}","{job_title}","{email}","{website}","{country}","{industry}","{budget}","{desc}"')
    
    # Add 30 deliberate duplicate rows (repeating existing email/company from earlier)
    for i in range(1, 31):
        domain, company_prefix = DOMAINS[i % len(DOMAINS)]
        dup_company = f"{company_prefix} Group {i}"
        dup_contact = f"Duplicate Contact {i}"
        dup_email = f"lead_{i}@{domain}" # Duplicate email
        website = f"https://{domain}"
        lines.append(f'"{dup_company}","{dup_contact}","CMO","{dup_email}","{website}","United States","Healthcare","50000","Duplicate test record"')

    # Add 20 invalid rows (missing both company and contact+email)
    for i in range(1, 21):
        lines.append('"",,"","","","","","","Missing company and email"')

    csv_text = "\n".join(lines)
    return csv_text, csv_text.encode("utf-8")

async def run_benchmark():
    print("=================================================================")
    print("   AI LEAD ANALYZER - 1,000-ROW DATASET BENCHMARK TEST")
    print("=================================================================")
    
    csv_text, file_bytes = generate_1000_row_healthcare_csv()
    filename = "healthcare_1000_leads.csv"
    print(f"Generated CSV size: {len(file_bytes) / 1024:.1f} KB, Total lines: {len(csv_text.splitlines())}")

    # 1. Test Preview Speed
    t0 = time.perf_counter()
    preview = LeadDatasetImporter.generate_preview(file_bytes, filename)
    preview_time = time.perf_counter() - t0
    print(f"\n[1] CSV Preview Generated in: {preview_time:.4f}s")
    print(f"    Detected Headers ({len(preview['detected_headers'])}): {preview['detected_headers']}")
    print(f"    Total Preview Rows: {preview['total_preview_rows']}")
    print(f"    Suggested Column Mappings: {preview['suggested_mappings']}")

    # 2. Test Full Async Concurrent Import & Verification
    print("\n[2] Executing Full Dataset Import & Concurrent Verification...")
    user_context = {
        "id": "da890374-b6b6-41ed-9185-ea8333711366",
        "email": "haider1.euroshub@gmail.com",
        "name": "Haider",
        "role": "admin"
    }
    
    existing_leads = await db.get_raw_leads()
    print(f"    Existing leads in DB before import: {len(existing_leads)}")

    t_start = time.perf_counter()
    result = await LeadDatasetImporter.process_import_async(
        file_bytes=file_bytes,
        filename=filename,
        column_mapping=preview["suggested_mappings"],
        existing_leads=existing_leads,
        auto_verify=True,
        source_name="Healthcare Benchmark Dataset",
        created_by_user_id=user_context["id"]
    )
    import_proc_time = time.perf_counter() - t_start

    print(f"\n--- VERIFICATION & PARSING PERFORMANCE ---")
    print(f"    Total Rows in CSV:       {result['total_rows']}")
    print(f"    Valid Rows:              {result['valid_rows']}")
    print(f"    Invalid Rows:            {result['invalid_rows']}")
    print(f"    Duplicate Rows Flagged:  {result['duplicate_rows']}")
    print(f"    Verified Leads:          {result['verified_rows']}")
    print(f"    Unverified Leads:        {result['unverified_rows']}")
    print(f"    Total Parsing & Concurrent Verification Time: {import_proc_time:.2f} seconds")
    print(f"    Average throughput: {result['total_rows'] / import_proc_time:.1f} rows/second")

    # 3. Test Bulk Database Insert
    print("\n[3] Executing Bulk Database Insertion...")
    leads_to_insert = [l for l in result["imported_leads"] if l.get("verification_status") != "DUPLICATE"]
    print(f"    Leads to insert: {len(leads_to_insert)}")

    t_db = time.perf_counter()
    inserted_leads = await db.create_leads_bulk(leads_to_insert, user_context, batch_size=200)
    db_insert_time = time.perf_counter() - t_db
    print(f"    Bulk DB Insertion Time for {len(inserted_leads)} leads: {db_insert_time:.2f} seconds")

    total_time = import_proc_time + db_insert_time
    print(f"\n=================================================================")
    print(f"   FINAL BENCHMARK RESULTS (1,000 ROWS)")
    print(f"=================================================================")
    print(f" * Total Rows Processed:    {result['total_rows']}")
    print(f" * Valid Rows:              {result['valid_rows']}")
    print(f" * Duplicate Rows:          {result['duplicate_rows']}")
    print(f" * Invalid Rows:            {result['invalid_rows']}")
    print(f" * Verified Rows:           {result['verified_rows']}")
    print(f" * Unverified Rows:         {result['unverified_rows']}")
    print(f" * Verification Time:       {import_proc_time:.2f}s")
    print(f" * DB Bulk Insert Time:     {db_insert_time:.2f}s")
    print(f" * TOTAL PROCESSING TIME:   {total_time:.2f}s")
    print(f"=================================================================")

    # 4. Verify Leads query endpoints
    print("\n[4] Verifying Discovery Search & Verified Leads retrieval...")
    discovery_res = await db.discover_leads(user_context, industry="Healthcare", page=1, page_size=10)
    print(f"    Found {discovery_res['total']} healthcare leads in Discovery catalog.")
    
    verified_res = await db.discover_leads(user_context, verification_status="VERIFIED", page=1, page_size=10)
    print(f"    Found {verified_res['total']} VERIFIED leads in system.")
    
    # Check sample lead verification score and details
    if inserted_leads:
        sample = inserted_leads[0]
        print(f"\n[5] Sample Verified Lead:")
        print(f"    Company: {sample.get('company_name')}")
        print(f"    Contact: {sample.get('contact_name')} ({sample.get('job_title')})")
        print(f"    Verification Status: {sample.get('verification_status')}")
        print(f"    Verification Score: {sample.get('verification_score')}/100")
        print(f"    Details: {sample.get('verification_details')}")

if __name__ == "__main__":
    from typing import Tuple
    asyncio.run(run_benchmark())
