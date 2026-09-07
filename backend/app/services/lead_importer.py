import io
import csv
import re
import asyncio
from typing import Dict, Any, List, Tuple, Optional, Set
from datetime import datetime, timezone
from urllib.parse import urlparse
from .lead_verifier import LeadVerificationEngine, VerificationCache, VERIFICATION_ACCEPTANCE_THRESHOLD, IMPORT_ACCEPTANCE_THRESHOLD
from .duplicate_checker import normalize_name
from ..models.enums import VerificationStatus, LeadStatus, LeadPriority

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

COLUMN_ALIASES = {
    "company_name": [
        "company", "company_name", "organization", "organization_name",
        "business", "business_name", "account", "firm", "enterprise",
        "company name", "organization name", "business name"
    ],
    "contact_name": [
        "name", "contact", "contact_name", "full_name", "fullname",
        "person", "lead_name", "contact name", "full name", "person name",
        "first_name", "lead name"
    ],
    "job_title": [
        "title", "job_title", "job title", "role", "position",
        "designation", "occupation", "job", "headline"
    ],
    "email": [
        "email", "email_address", "mail", "contact_email", "e-mail",
        "email address", "work_email", "primary_email"
    ],
    "phone": [
        "phone", "phone_number", "telephone", "mobile", "cell",
        "contact_phone", "phone number", "mobile_number", "tel"
    ],
    "website": [
        "website", "url", "domain", "web", "site", "website_url",
        "company_website", "web page", "web_url", "homepage"
    ],
    "country": [
        "country", "nation", "location", "geo", "region", "country_name",
        "territory", "state_country"
    ],
    "industry": [
        "industry", "sector", "vertical", "category", "business_type",
        "niche", "industry_name"
    ],
    "budget": [
        "budget", "deal_size", "value", "revenue", "amount", "budget_amount", "est_budget"
    ],
    "project_title": [
        "project", "project_title", "opportunity", "requirement", "project title", "deal_title"
    ],
    "project_description": [
        "description", "details", "notes", "summary", "project_description",
        "overview", "comment", "needs"
    ]
}

def normalize_email(email: Optional[str]) -> Optional[str]:
    if not email or not isinstance(email, str):
        return None
    clean = email.strip().lower()
    return clean if "@" in clean else None

def normalize_url(url: Optional[str]) -> Optional[str]:
    if not url or not isinstance(url, str):
        return None
    clean = url.strip()
    if not clean:
        return None
    if not clean.startswith(("http://", "https://")):
        clean = "https://" + clean
    try:
        parsed = urlparse(clean)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = parsed.path.rstrip("/")
        return f"https://{netloc}{path}" if netloc else None
    except Exception:
        return clean.lower()

def normalize_phone_number(phone: Optional[str]) -> Optional[str]:
    if not phone or not isinstance(phone, str):
        return None
    clean = phone.strip()
    has_plus = clean.startswith("+")
    digits = re.sub(r"[^\d]", "", clean)
    if not digits:
        return None
    return f"+{digits}" if has_plus else digits

def suggest_column_mappings(detected_headers: List[str]) -> Dict[str, str]:
    mappings = {}
    used_targets = set()

    for header in detected_headers:
        norm_h = header.strip().lower().replace("_", " ").replace("-", " ")
        matched_target = None

        for target_field, aliases in COLUMN_ALIASES.items():
            if target_field in used_targets:
                continue
            for alias in aliases:
                norm_alias = alias.lower().replace("_", " ")
                if norm_h == norm_alias or norm_h == target_field:
                    matched_target = target_field
                    break
            if matched_target:
                break

        if matched_target:
            mappings[header] = matched_target
            used_targets.add(matched_target)
        else:
            mappings[header] = ""

    return mappings

def parse_file_to_rows(file_bytes: bytes, filename: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    fn_lower = filename.lower()

    if fn_lower.endswith(".xlsx") or fn_lower.endswith(".xls"):
        if not HAS_OPENPYXL:
            raise ValueError("Excel parsing library (openpyxl) is not installed.")
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        try:
            header_row = next(rows_iter)
        except StopIteration:
            return [], []

        headers = [str(col).strip() if col is not None else f"Column_{idx+1}" for idx, col in enumerate(header_row)]
        all_rows = []
        for row in rows_iter:
            if not any(row):
                continue
            row_dict = {}
            for idx, val in enumerate(row):
                if idx < len(headers):
                    row_dict[headers[idx]] = str(val).strip() if val is not None else ""
            if any(row_dict.values()):
                all_rows.append(row_dict)
        return headers, all_rows

    # Default CSV parser with multiple encoding attempts
    decoded_text = None
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            decoded_text = file_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if decoded_text is None:
        decoded_text = file_bytes.decode("utf-8", errors="replace")

    # Detect delimiter
    sample = decoded_text[:2048]
    delimiter = ","
    if ";" in sample and sample.count(";") > sample.count(","):
        delimiter = ";"
    elif "\t" in sample and sample.count("\t") > sample.count(","):
        delimiter = "\t"

    reader = csv.DictReader(io.StringIO(decoded_text), delimiter=delimiter)
    headers = [h.strip() for h in (reader.fieldnames or []) if h]
    all_rows = []
    for r in reader:
        clean_row = {k.strip(): (v.strip() if v else "") for k, v in r.items() if k}
        if any(clean_row.values()):
            all_rows.append(clean_row)

    return headers, all_rows

class LeadDatasetImporter:
    """
    Handles CSV/XLSX preview, normalization, deduplication, and asynchronous concurrent verification.
    """

    @classmethod
    def generate_preview(cls, file_bytes: bytes, filename: str, max_preview: int = 10) -> Dict[str, Any]:
        headers, all_rows = parse_file_to_rows(file_bytes, filename)
        suggested = suggest_column_mappings(headers)
        return {
            "total_preview_rows": len(all_rows),
            "detected_headers": headers,
            "suggested_mappings": suggested,
            "preview_rows": all_rows[:max_preview]
        }

    @classmethod
    async def process_import_async(
        cls,
        file_bytes: bytes,
        filename: str,
        column_mapping: Dict[str, str],
        existing_leads: List[Dict[str, Any]],
        auto_verify: bool = True,
        source_name: Optional[str] = "CSV Import",
        created_by_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        headers, all_rows = parse_file_to_rows(file_bytes, filename)

        # Build the set of canonical dataset fields that are actually mapped.
        # This is passed to the verification engine so absent columns do NOT
        # penalise leads — their weight is redistributed to applicable signals.
        target_to_source: Dict[str, str] = {}
        for src_col, tgt_field in column_mapping.items():
            if tgt_field:
                target_to_source[tgt_field] = src_col

        dataset_fields: Set[str] = set(target_to_source.keys())
        # company_name is always considered present (it's either mapped or synthesised)
        dataset_fields.add("company_name")

        # Build deduplication indexes from existing database leads
        existing_emails: Set[str] = set()
        existing_companies: Set[str] = set()
        for lead in existing_leads:
            em = normalize_email(lead.get("email"))
            if em:
                existing_emails.add(em)
            comp_norm = normalize_name(lead.get("company_name", ""))
            if comp_norm:
                existing_companies.add(comp_norm)

        # Track duplicates within the current import batch
        batch_seen_emails: Set[str] = set()
        batch_seen_companies: Set[str] = set()

        imported_leads: List[Dict[str, Any]] = []
        leads_to_verify: List[Tuple[int, Dict[str, Any]]] = []

        valid_rows = 0
        invalid_rows = 0
        duplicate_rows = 0
        verified_rows = 0
        unverified_rows = 0

        for row_idx, row in enumerate(all_rows):
            company_raw  = row.get(target_to_source.get("company_name", ""), "").strip()
            contact_raw  = row.get(target_to_source.get("contact_name", ""), "").strip()
            job_title_raw = row.get(target_to_source.get("job_title", ""), "").strip()
            email_raw    = row.get(target_to_source.get("email", ""), "").strip()
            phone_raw    = row.get(target_to_source.get("phone", ""), "").strip()
            website_raw  = row.get(target_to_source.get("website", ""), "").strip()
            country_raw  = row.get(target_to_source.get("country", ""), "").strip()
            industry_raw = row.get(target_to_source.get("industry", ""), "").strip()
            budget_raw   = row.get(target_to_source.get("budget", ""), "").strip()
            proj_title_raw = row.get(target_to_source.get("project_title", ""), "").strip()
            proj_desc_raw  = row.get(target_to_source.get("project_description", ""), "").strip()

            # Basic validity: must have at least a company name OR (contact + email)
            if not company_raw and not (contact_raw and email_raw):
                invalid_rows += 1
                continue

            if not company_raw and contact_raw:
                company_raw = f"{contact_raw} Org"

            valid_rows += 1

            # Normalization
            norm_email_val = normalize_email(email_raw)
            norm_phone_val = normalize_phone_number(phone_raw)
            norm_url_val   = normalize_url(website_raw)
            norm_comp_val  = normalize_name(company_raw)

            # Parse budget
            parsed_budget = 0.0
            if budget_raw:
                clean_b = re.sub(r"[^\d.]", "", budget_raw)
                try:
                    parsed_budget = float(clean_b)
                except ValueError:
                    parsed_budget = 0.0

            # ---- Duplicate Check ----
            is_dup = False
            dup_reason = ""

            if norm_email_val:
                if norm_email_val in existing_emails or norm_email_val in batch_seen_emails:
                    is_dup = True
                    dup_reason = f"Duplicate email address: {norm_email_val}"

            if not is_dup and norm_comp_val:
                if norm_comp_val in existing_companies or norm_comp_val in batch_seen_companies:
                    is_dup = True
                    dup_reason = f"Duplicate company name: {company_raw}"

            if is_dup:
                duplicate_rows += 1
                v_status = VerificationStatus.DUPLICATE.value
                v_score = 0
                v_details = {
                    "score": 0,
                    "status": "DUPLICATE",
                    "reason": dup_reason,
                    "last_verified_at": datetime.now(timezone.utc).isoformat(),
                    "acceptance_threshold": IMPORT_ACCEPTANCE_THRESHOLD,
                }
            else:
                if norm_email_val:
                    batch_seen_emails.add(norm_email_val)
                if norm_comp_val:
                    batch_seen_companies.add(norm_comp_val)

                v_status = VerificationStatus.UNVERIFIED.value
                v_score = 0
                v_details = None

            lead_record: Dict[str, Any] = {
                "company_name": company_raw,
                "contact_name": contact_raw or None,
                "job_title": job_title_raw or None,
                "email": email_raw or None,
                "phone": phone_raw or None,
                "website": norm_url_val or website_raw or None,
                "industry": industry_raw or None,
                "country": country_raw.title() if country_raw else None,
                "source": source_name or "CSV Import",
                "custom_source": filename,
                "project_title": proj_title_raw or (f"Discovery: {company_raw}"),
                "project_description": proj_desc_raw or None,
                "budget": parsed_budget,
                "currency": "USD",
                "priority": LeadPriority.MEDIUM.value,
                "status": LeadStatus.NEW.value,
                "verification_status": v_status,
                "verification_score": v_score,
                "verification_details": v_details,
                "last_verified_at": datetime.now(timezone.utc).isoformat() if is_dup else None,
                "is_candidate": True,
                "normalized_email": norm_email_val,
                "normalized_phone": norm_phone_val,
                "normalized_company": norm_comp_val,
                "source_record_id": f"row_{row_idx + 1}",
                "_row_number": row_idx + 1,   # internal, stripped before DB insert
                "created_by": created_by_user_id,
            }

            lead_idx = len(imported_leads)
            imported_leads.append(lead_record)

            if not is_dup and auto_verify:
                leads_to_verify.append((lead_idx, {
                    "company_name": company_raw,
                    "contact_name": contact_raw,
                    "job_title": job_title_raw,
                    "email": email_raw,
                    "phone": phone_raw,
                    "website": norm_url_val or website_raw,
                    "industry": industry_raw,
                    "country": country_raw,
                    "source": source_name or "CSV Import",
                }))

        # ----------------------------------------------------------------
        # Concurrent async verification
        # ----------------------------------------------------------------
        if auto_verify and leads_to_verify:
            cache = VerificationCache()
            payloads = [item[1] for item in leads_to_verify]
            v_results = await LeadVerificationEngine.verify_leads_batch_async(
                payloads, concurrency=20, cache=cache
            )

            for (idx, _), v_res in zip(leads_to_verify, v_results):
                st = v_res["verification_status"]
                sc = v_res["verification_score"]
                imported_leads[idx]["verification_status"] = st
                imported_leads[idx]["verification_score"]  = sc
                imported_leads[idx]["verification_details"] = v_res["verification_details"]
                imported_leads[idx]["last_verified_at"]     = v_res["last_verified_at"]

        # ----------------------------------------------------------------
        # 70% Acceptance Gate — split into accepted / rejected
        # ----------------------------------------------------------------
        accepted_leads: List[Dict[str, Any]] = []
        rejected_leads: List[Dict[str, Any]] = []
        rejection_details: List[Dict[str, Any]] = []

        for lead in imported_leads:
            v_stat  = lead.get("verification_status", "UNVERIFIED")
            v_score = lead.get("verification_score", 0)

            if v_stat == VerificationStatus.DUPLICATE.value:
                # Duplicates count separately — not accepted or rejected
                continue

            if v_score >= IMPORT_ACCEPTANCE_THRESHOLD:
                lead["_accepted"] = True
                accepted_leads.append(lead)
                if v_stat == VerificationStatus.VERIFIED.value:
                    verified_rows += 1
                else:
                    unverified_rows += 1
            else:
                lead["_accepted"] = False
                rejected_leads.append(lead)

                # Build human-readable rejection reasons from the checks dict
                checks = (lead.get("verification_details") or {}).get("checks", {})
                reasons: List[str] = []
                for check_key, check_val in checks.items():
                    if isinstance(check_val, dict) and check_val.get("passed") is False:
                        detail = check_val.get("detail", check_key)
                        reasons.append(detail)
                if not reasons:
                    reasons = [f"Verification score {v_score}% is below the {IMPORT_ACCEPTANCE_THRESHOLD}% threshold"]

                rejection_details.append({
                    "row_number": lead.get("_row_number", 0),
                    "company_name": lead.get("company_name", "Unknown"),
                    "score": v_score,
                    "reasons": reasons,
                })

        return {
            "total_rows": len(all_rows),
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "duplicate_rows": duplicate_rows,
            "verified_rows": verified_rows,
            "unverified_rows": unverified_rows,
            "accepted_rows": len(accepted_leads),
            "rejected_rows": len(rejected_leads),
            "rejection_threshold": IMPORT_ACCEPTANCE_THRESHOLD,
            "rejection_details": rejection_details,
            "imported_leads": imported_leads,    # all leads including rejected (for audit)
            "accepted_leads": accepted_leads,     # only these go to DB
            "rejected_leads": rejected_leads,     # never inserted
        }

    @classmethod
    def process_import(
        cls,
        file_bytes: bytes,
        filename: str,
        column_mapping: Dict[str, str],
        existing_leads: List[Dict[str, Any]],
        auto_verify: bool = True,
        source_name: Optional[str] = "CSV Import",
        created_by_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous wrapper for process_import_async."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In an already running event loop, run in a separate task/thread or use nest_asyncio if available
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run,
                        cls.process_import_async(
                            file_bytes, filename, column_mapping, existing_leads,
                            auto_verify, source_name, created_by_user_id
                        )
                    ).result()
            else:
                return loop.run_until_complete(
                    cls.process_import_async(
                        file_bytes, filename, column_mapping, existing_leads,
                        auto_verify, source_name, created_by_user_id
                    )
                )
        except Exception:
            return asyncio.run(
                cls.process_import_async(
                    file_bytes, filename, column_mapping, existing_leads,
                    auto_verify, source_name, created_by_user_id
                )
            )
