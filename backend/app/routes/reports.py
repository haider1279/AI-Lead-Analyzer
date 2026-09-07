import io
import csv
from fastapi import APIRouter, Depends, Response
from typing import Dict, Any
from ..db.database import db
from ..auth.jwt import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/summary")
async def get_reports_summary(current_user: Dict[str, Any] = Depends(get_current_user)):
    leads = await db.list_leads(current_user=current_user)

    total_leads = len(leads)
    won_leads = [l for l in leads if l.get("status") == "WON"]
    lost_leads = [l for l in leads if l.get("status") == "LOST"]
    active_leads = [l for l in leads if l.get("status") not in ["WON", "LOST"]]

    total_pipeline_val = sum(float(l.get("budget", 0) or 0) for l in active_leads)
    won_val = sum(float(l.get("budget", 0) or 0) for l in won_leads)
    lost_val = sum(float(l.get("budget", 0) or 0) for l in lost_leads)

    closed_count = len(won_leads) + len(lost_leads)
    conversion_rate = round((len(won_leads) / closed_count * 100), 1) if closed_count > 0 else 0.0

    # Source efficiency
    sources_stat: Dict[str, Dict[str, Any]] = {}
    for l in leads:
        src = l.get("source") or "Other"
        if src not in sources_stat:
            sources_stat[src] = {"source": src, "total": 0, "won": 0, "lost": 0, "pipeline_value": 0.0, "won_value": 0.0}
        sources_stat[src]["total"] += 1
        sources_stat[src]["pipeline_value"] += float(l.get("budget", 0) or 0)
        if l.get("status") == "WON":
            sources_stat[src]["won"] += 1
            sources_stat[src]["won_value"] += float(l.get("budget", 0) or 0)
        elif l.get("status") == "LOST":
            sources_stat[src]["lost"] += 1

    source_efficiency = []
    for s_name, data in sources_stat.items():
        closed_s = data["won"] + data["lost"]
        rate = round((data["won"] / closed_s * 100), 1) if closed_s > 0 else 0.0
        source_efficiency.append({
            "source": s_name,
            "total_leads": data["total"],
            "won_leads": data["won"],
            "conversion_rate": rate,
            "total_value": data["pipeline_value"],
            "won_value": data["won_value"]
        })

    return {
        "total_leads": total_leads,
        "active_leads_count": len(active_leads),
        "won_leads_count": len(won_leads),
        "lost_leads_count": len(lost_leads),
        "conversion_rate": conversion_rate,
        "total_pipeline_value": total_pipeline_val,
        "won_pipeline_value": won_val,
        "lost_pipeline_value": lost_val,
        "source_efficiency": source_efficiency
    }

def sanitize_csv_cell(val: Any) -> str:
    """Sanitize cell value to prevent CSV formula injection vulnerability."""
    if val is None:
        return ""
    s = str(val)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s

@router.get("/export-csv")
async def export_leads_csv(current_user: Dict[str, Any] = Depends(get_current_user)):
    leads = await db.list_leads(current_user=current_user)

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Lead ID",
        "Company Name",
        "Contact Name",
        "Job Title",
        "Email",
        "Phone",
        "Website",
        "Industry",
        "Country",
        "Source",
        "Project Title",
        "Budget",
        "Currency",
        "Status",
        "Priority",
        "Verification Status",
        "Verification Score",
        "Assigned Employee",
        "Follow-Up Date",
        "Lead Score",
        "Created At"
    ])

    for l in leads:
        assigned_name = l.get("assigned_user", {}).get("name") if l.get("assigned_user") else "Unassigned"
        writer.writerow([
            sanitize_csv_cell(l.get("id", "")),
            sanitize_csv_cell(l.get("company_name", "")),
            sanitize_csv_cell(l.get("contact_name", "")),
            sanitize_csv_cell(l.get("job_title", "")),
            sanitize_csv_cell(l.get("email", "")),
            sanitize_csv_cell(l.get("phone", "")),
            sanitize_csv_cell(l.get("website", "")),
            sanitize_csv_cell(l.get("industry", "")),
            sanitize_csv_cell(l.get("country", "")),
            sanitize_csv_cell(l.get("source", "")),
            sanitize_csv_cell(l.get("project_title", "")),
            sanitize_csv_cell(l.get("budget", 0.0)),
            sanitize_csv_cell(l.get("currency", "USD")),
            sanitize_csv_cell(l.get("status", "")),
            sanitize_csv_cell(l.get("priority", "")),
            sanitize_csv_cell(l.get("verification_status", "UNVERIFIED")),
            sanitize_csv_cell(l.get("verification_score", 0)),
            sanitize_csv_cell(assigned_name),
            sanitize_csv_cell(l.get("follow_up_date", "")),
            sanitize_csv_cell(l.get("lead_score", "")),
            sanitize_csv_cell(l.get("created_at", ""))
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=euroshub_leads_export.csv"
        }
    )

