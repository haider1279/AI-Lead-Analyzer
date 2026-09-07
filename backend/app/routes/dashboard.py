from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime, timezone
from ..db.database import db
from ..auth.jwt import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
async def get_dashboard_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    leads = await db.list_leads(current_user=current_user)
    activities = await db.get_raw_activities()
    tasks = await db.list_tasks(current_user=current_user)
    
    now = datetime.now(timezone.utc)
    today_date = now.date()

    total_leads = len(leads)
    new_leads = sum(1 for l in leads if l.get("status") == "NEW")
    contacted = sum(1 for l in leads if l.get("status") == "CONTACTED")
    qualified = sum(1 for l in leads if l.get("status") == "QUALIFIED")
    proposals_sent = sum(1 for l in leads if l.get("status") == "PROPOSAL_SENT")
    negotiation = sum(1 for l in leads if l.get("status") == "NEGOTIATION")
    won_leads = sum(1 for l in leads if l.get("status") == "WON")
    lost_leads = sum(1 for l in leads if l.get("status") == "LOST")

    active_opportunities = new_leads + contacted + qualified + proposals_sent + negotiation

    # Conversion rate
    finished_leads = won_leads + lost_leads
    conversion_rate = round((won_leads / finished_leads * 100), 1) if finished_leads > 0 else (round((won_leads / total_leads * 100), 1) if total_leads > 0 else 0.0)

    # Pipeline values
    total_pipeline_value = sum(float(l.get("budget", 0) or 0) for l in leads if l.get("status") in ["NEW", "CONTACTED", "QUALIFIED", "PROPOSAL_SENT", "NEGOTIATION"])
    won_pipeline_value = sum(float(l.get("budget", 0) or 0) for l in leads if l.get("status") == "WON")

    # Follow-ups counts
    follow_ups_today = 0
    follow_ups_upcoming = 0
    follow_ups_overdue = 0

    urgent_follow_ups = []

    for l in leads:
        f_date_str = l.get("follow_up_date")
        if f_date_str and l.get("status") not in ["WON", "LOST"]:
            try:
                f_date = datetime.fromisoformat(f_date_str.replace('Z', '+00:00'))
                state = ""
                if f_date.date() < today_date:
                    follow_ups_overdue += 1
                    state = "overdue"
                elif f_date.date() == today_date:
                    follow_ups_today += 1
                    state = "today"
                else:
                    follow_ups_upcoming += 1
                    state = "upcoming"

                if state in ["overdue", "today"]:
                    urgent_follow_ups.append({
                        "id": l["id"],
                        "company_name": l["company_name"],
                        "project_title": l.get("project_title"),
                        "status": l.get("status"),
                        "follow_up_date": f_date_str,
                        "state": state,
                        "priority": l.get("priority"),
                        "assigned_to": l.get("assigned_to"),
                        "assigned_user": l.get("assigned_user")
                    })
            except Exception:
                pass

    # Status distribution
    status_order = ["NEW", "CONTACTED", "QUALIFIED", "PROPOSAL_SENT", "NEGOTIATION", "WON", "LOST"]
    leads_by_status = []
    for st in status_order:
        st_leads = [l for l in leads if l.get("status") == st]
        leads_by_status.append({
            "status": st,
            "count": len(st_leads),
            "value": sum(float(l.get("budget", 0) or 0) for l in st_leads)
        })

    # Source distribution
    source_counts: Dict[str, Dict[str, Any]] = {}
    for l in leads:
        src = l.get("source") or "Other"
        if src not in source_counts:
            source_counts[src] = {"source": src, "count": 0, "value": 0.0}
        source_counts[src]["count"] += 1
        source_counts[src]["value"] += float(l.get("budget", 0) or 0)
    leads_by_source = list(source_counts.values())

    # Recent activities (filtered by access)
    recent_activities = []
    lead_ids = set(l["id"] for l in leads)
    all_profiles = {p["id"]: p for p in await db.list_profiles()}
    for a in activities:
        if a.get("lead_id") in lead_ids:
            a_copy = dict(a)
            a_copy["user"] = all_profiles.get(a.get("user_id")) if a.get("user_id") else None
            for l in leads:
                if l["id"] == a.get("lead_id"):
                    a_copy["lead_company_name"] = l["company_name"]
                    break
            recent_activities.append(a_copy)
            if len(recent_activities) >= 8:
                break

    # Tasks stats
    pending_tasks = [t for t in tasks if t.get("status") != "COMPLETED"]

    # Verification stats
    verified_leads_count = sum(1 for l in leads if l.get("verification_status") == "VERIFIED")
    partially_verified_count = sum(1 for l in leads if l.get("verification_status") == "PARTIALLY_VERIFIED")
    unverified_leads_count = sum(1 for l in leads if l.get("verification_status") in ["UNVERIFIED", None])
    total_verifiable = total_leads if total_leads > 0 else 1
    verification_rate = round(((verified_leads_count + (partially_verified_count * 0.5)) / total_verifiable) * 100, 1) if total_leads > 0 else 0.0

    return {
        "total_leads": total_leads,
        "new_leads": new_leads,
        "active_opportunities": active_opportunities,
        "proposals_sent": proposals_sent,
        "negotiations": negotiation,
        "won_leads": won_leads,
        "lost_leads": lost_leads,
        "conversion_rate": conversion_rate,
        "total_pipeline_value": total_pipeline_value,
        "won_pipeline_value": won_pipeline_value,
        "follow_ups_today": follow_ups_today,
        "follow_ups_upcoming": follow_ups_upcoming,
        "follow_ups_overdue": follow_ups_overdue,
        "urgent_follow_ups": urgent_follow_ups[:6],
        "pending_tasks": pending_tasks[:6],
        "leads_by_status": leads_by_status,
        "leads_by_source": leads_by_source,
        "recent_activities": recent_activities,
        "verified_leads_count": verified_leads_count,
        "partially_verified_count": partially_verified_count,
        "unverified_leads_count": unverified_leads_count,
        "verification_rate": verification_rate
    }

