import re
from typing import List, Dict, Any, Optional
from ..models.schemas import DuplicateMatch

def normalize_name(name: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', name.lower())
    # Remove common corporate suffixes
    cleaned = re.sub(r'\b(ltd|limited|inc|corp|corporation|llc|gmbh|co|sa|hub|tech|technologies)\b', '', cleaned)
    return ' '.join(cleaned.split())

def check_duplicates(company_name: str, email: Optional[str], all_leads: List[Dict[str, Any]], exclude_id: Optional[str] = None) -> List[DuplicateMatch]:
    matches = []
    norm_input_company = normalize_name(company_name)
    input_email_clean = (email or "").strip().lower()

    for lead in all_leads:
        lead_id = str(lead.get("id"))
        if exclude_id and lead_id == str(exclude_id):
            continue

        existing_company = lead.get("company_name", "")
        norm_existing_company = normalize_name(existing_company)
        existing_email = (lead.get("email") or "").strip().lower()

        reasons = []

        if input_email_clean and existing_email and input_email_clean == existing_email:
            reasons.append(f"Identical contact email: {existing_email}")

        if norm_input_company and norm_existing_company:
            if norm_input_company == norm_existing_company:
                reasons.append(f"Exact company match: '{existing_company}'")
            elif norm_input_company in norm_existing_company or norm_existing_company in norm_input_company:
                reasons.append(f"Similar company name: '{existing_company}'")

        if reasons:
            matches.append(DuplicateMatch(
                lead_id=lead_id,
                company_name=existing_company,
                email=lead.get("email"),
                contact_name=lead.get("contact_name"),
                status=lead.get("status", "NEW"),
                match_reason=" & ".join(reasons)
            ))

    return matches
