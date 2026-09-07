import os
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timezone
from enum import Enum
from ..utils.config import settings
from .memory_store import store

def get_supabase_client():
    has_url = bool(settings.SUPABASE_URL and settings.SUPABASE_URL.strip())
    has_key = bool(settings.SUPABASE_KEY and settings.SUPABASE_KEY.strip())

    if has_url or has_key:
        if not (has_url and has_key):
            raise ValueError("[DB Error] Supabase configuration incomplete: Both SUPABASE_URL and SUPABASE_KEY must be provided.")
        try:
            from supabase import create_client, Client
            client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            return client
        except Exception as e:
            print(f"[DB Error] Failed to initialize Supabase client: {e}")
            raise RuntimeError(f"Failed to initialize Supabase client: {e}") from e
    return None

NEW_LEAD_COLS = {
    "job_title", "verification_status", "verification_score", "verification_details",
    "last_verified_at", "is_candidate", "normalized_email", "normalized_phone",
    "normalized_company", "source_record_id"
}

def _serialize_for_db(record: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Python datetime/date/Enum objects to JSON-serializable types for Supabase HTTP requests."""
    result = {}
    for k, v in record.items():
        if isinstance(v, datetime):
            result[k] = v.isoformat()
        elif isinstance(v, date):
            result[k] = v.isoformat()
        elif isinstance(v, Enum):
            result[k] = v.value
        else:
            result[k] = v
    return result

def _format_lead_out(lead: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not lead:
        return lead
    l = dict(lead)
    ai_a = l.get("ai_analysis")
    if isinstance(ai_a, dict) and "_discovery" in ai_a:
        disc = ai_a["_discovery"]
        for col in NEW_LEAD_COLS:
            if l.get(col) is None and col in disc:
                l[col] = disc[col]
    if not l.get("verification_status"):
        l["verification_status"] = "UNVERIFIED"
    if l.get("verification_score") is None:
        l["verification_score"] = 0
    if l.get("is_candidate") is None:
        l["is_candidate"] = False
    return l


class DatabaseRepository:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.store = store


    # --- Profiles ---
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("profiles").select("*").eq("id", user_id).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                print(f"[DB] Error in get_profile: {e}")
                raise e
            return None
        return self.store.get_profile(user_id)

    async def get_profile_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("profiles").select("*").eq("email", email.lower().strip()).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                print(f"[DB] Error in get_profile_by_email: {e}")
                raise e
            return None
        return self.store.get_profile_by_email(email)

    async def list_profiles(self) -> List[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("profiles").select("*").execute()
                return res.data or []
            except Exception as e:
                print(f"[DB] Error in list_profiles: {e}")
                raise e
        return list(self.store.profiles)

    async def create_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        if self.supabase:
            try:
                res = self.supabase.table("profiles").insert(profile).execute()
                return res.data[0]
            except Exception as e:
                print(f"[DB] Error in create_profile: {e}")
                raise e
        else:
            return self.store.create_or_update_profile(profile)

    async def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("profiles").update(updates).eq("id", user_id).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                print(f"[DB] Error in update_profile: {e}")
                raise e
            return None
        else:
            p = self.store.get_profile(user_id)
            if p:
                p.update(updates)
                p["updated_at"] = datetime.now(timezone.utc).isoformat()
                return p
        return None

    # --- Lead Sources ---
    async def list_lead_sources(self) -> List[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("lead_sources").select("*").eq("is_active", True).execute()
                return res.data or []
            except Exception as e:
                print(f"[DB] Error in list_lead_sources: {e}")
                raise e
        return [s for s in self.store.lead_sources if s.get("is_active", True)]

    async def create_lead_source(self, name: str) -> Dict[str, Any]:
        if self.supabase:
            try:
                res = self.supabase.table("lead_sources").insert({"name": name.strip()}).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                print(f"[DB] Error in create_lead_source: {e}")
                raise e
        else:
            source = {
                "id": str(uuid.uuid4()),
                "name": name.strip(),
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.store.lead_sources.append(source)
            return source

    async def delete_lead_source(self, source_id: str) -> bool:
        if self.supabase:
            try:
                self.supabase.table("lead_sources").delete().eq("id", source_id).execute()
                return True
            except Exception as e:
                print(f"[DB] Error in delete_lead_source: {e}")
                raise e
        else:
            for i, s in enumerate(self.store.lead_sources):
                if str(s.get("id")) == str(source_id):
                    self.store.lead_sources.pop(i)
                    return True
        return False

    # --- Leads ---
    async def get_raw_leads(self) -> List[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("leads").select("*").execute()
                return res.data or []
            except Exception as e:
                print(f"[DB] Error in get_raw_leads: {e}")
                raise e
        return self.store.leads

    async def list_leads(self, current_user: Dict[str, Any], search: Optional[str] = None,
                         status: Optional[str] = None, source: Optional[str] = None,
                         priority: Optional[str] = None, assigned_to: Optional[str] = None,
                         follow_up_state: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.supabase:
            try:
                query = self.supabase.table("leads").select("*")
                if current_user.get("role") != "admin":
                    user_id = str(current_user.get("id"))
                    query = query.or_(f"assigned_to.eq.{user_id},created_by.eq.{user_id}")
                
                if status:
                    query = query.eq("status", status)
                if source:
                    query = query.eq("source", source)
                if priority:
                    query = query.eq("priority", priority)
                if assigned_to:
                    query = query.eq("assigned_to", assigned_to)
                
                if search:
                    s = search.strip()
                    query = query.or_(f"company_name.ilike.%{s}%,contact_name.ilike.%{s}%,email.ilike.%{s}%,project_title.ilike.%{s}%")
                
                res = query.order("created_at", desc=True).execute()
                leads = res.data or []

                now = datetime.now(timezone.utc)
                today_date = now.date()
                filtered = []
                
                all_profiles = {p["id"]: p for p in await self.list_profiles()}
                
                activities_count_res = self.supabase.table("activities").select("lead_id").execute()
                tasks_count_res = self.supabase.table("tasks").select("lead_id").execute()
                
                activities_map = {}
                for a in (activities_count_res.data or []):
                    lid = a.get("lead_id")
                    if lid:
                        activities_map[lid] = activities_map.get(lid, 0) + 1
                        
                tasks_map = {}
                for t in (tasks_count_res.data or []):
                    lid = t.get("lead_id")
                    if lid:
                        tasks_map[lid] = tasks_map.get(lid, 0) + 1

                for lead in leads:
                    if follow_up_state:
                        f_date_str = lead.get("follow_up_date")
                        if not f_date_str:
                            continue
                        try:
                            f_date = datetime.fromisoformat(f_date_str.replace('Z', '+00:00'))
                            if follow_up_state == "overdue" and f_date.date() < today_date:
                                pass
                            elif follow_up_state == "today" and f_date.date() == today_date:
                                pass
                            elif follow_up_state == "upcoming" and f_date.date() > today_date:
                                pass
                            else:
                                continue
                        except Exception:
                            continue
                    
                    lead["assigned_user"] = all_profiles.get(lead.get("assigned_to")) if lead.get("assigned_to") else None
                    lead["creator_user"] = all_profiles.get(lead.get("created_by")) if lead.get("created_by") else None
                    lead["activities_count"] = activities_map.get(lead["id"], 0)
                    lead["tasks_count"] = tasks_map.get(lead["id"], 0)
                    filtered.append(_format_lead_out(lead))
                
                return filtered
            except Exception as e:
                print(f"[DB] Error in list_leads: {e}")
                raise e
        else:
            is_admin = current_user.get("role") == "admin"
            user_id = str(current_user.get("id"))
            results = []
            now = datetime.now(timezone.utc)
            today_date = now.date()

            for lead in self.store.leads:
                if not is_admin:
                    lead_assigned = str(lead.get("assigned_to") or "")
                    lead_creator = str(lead.get("created_by") or "")
                    if lead_assigned != user_id and lead_creator != user_id:
                        continue

                if status and lead.get("status") != status:
                    continue
                if source and lead.get("source") != source:
                    continue
                if priority and lead.get("priority") != priority:
                    continue
                if assigned_to and str(lead.get("assigned_to") or "") != assigned_to:
                    continue

                if follow_up_state:
                    f_date_str = lead.get("follow_up_date")
                    if not f_date_str:
                        continue
                    try:
                        f_date = datetime.fromisoformat(f_date_str.replace('Z', '+00:00'))
                        if follow_up_state == "overdue" and f_date.date() < today_date:
                            pass
                        elif follow_up_state == "today" and f_date.date() == today_date:
                            pass
                        elif follow_up_state == "upcoming" and f_date.date() > today_date:
                            pass
                        else:
                            continue
                    except Exception:
                        continue

                if search:
                    s = search.lower().strip()
                    match = (
                        s in (lead.get("company_name") or "").lower() or
                        s in (lead.get("contact_name") or "").lower() or
                        s in (lead.get("email") or "").lower() or
                        s in (lead.get("project_title") or "").lower()
                    )
                    if not match:
                        continue

                lead_copy = _format_lead_out(dict(lead))
                lead_copy["assigned_user"] = self.store.get_profile(lead.get("assigned_to")) if lead.get("assigned_to") else None
                lead_copy["creator_user"] = self.store.get_profile(lead.get("created_by")) if lead.get("created_by") else None
                lead_copy["activities_count"] = sum(1 for a in self.store.activities if str(a.get("lead_id")) == str(lead.get("id")))
                lead_copy["tasks_count"] = sum(1 for t in self.store.tasks if str(t.get("lead_id")) == str(lead.get("id")))
                results.append(lead_copy)

            results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return results

    async def get_lead(self, lead_id: str, current_user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("leads").select("*").eq("id", lead_id).execute()
                if not res.data:
                    return None
                lead = _format_lead_out(res.data[0])
                
                if current_user.get("role") != "admin":
                    user_id = str(current_user.get("id"))
                    lead_assigned = str(lead.get("assigned_to") or "")
                    lead_creator = str(lead.get("created_by") or "")
                    if lead_assigned != user_id and lead_creator != user_id:
                        return None
                
                all_profiles = {p["id"]: p for p in await self.list_profiles()}
                lead["assigned_user"] = all_profiles.get(lead.get("assigned_to")) if lead.get("assigned_to") else None
                lead["creator_user"] = all_profiles.get(lead.get("created_by")) if lead.get("created_by") else None
                
                act_res = self.supabase.table("activities").select("id", count="exact").eq("lead_id", lead_id).execute()
                lead["activities_count"] = act_res.count if hasattr(act_res, "count") else len(act_res.data or [])
                
                tsk_res = self.supabase.table("tasks").select("id", count="exact").eq("lead_id", lead_id).execute()
                lead["tasks_count"] = tsk_res.count if hasattr(tsk_res, "count") else len(tsk_res.data or [])
                
                return lead
            except Exception as e:
                print(f"[DB] Error in get_lead: {e}")
                raise e

        else:
            is_admin = current_user.get("role") == "admin"
            user_id = str(current_user.get("id"))

            for lead in self.store.leads:
                if str(lead.get("id")) == str(lead_id):
                    if not is_admin:
                        lead_assigned = str(lead.get("assigned_to") or "")
                        lead_creator = str(lead.get("created_by") or "")
                        if lead_assigned != user_id and lead_creator != user_id:
                            return None
                    
                    lead_copy = dict(lead)
                    lead_copy["assigned_user"] = self.store.get_profile(lead.get("assigned_to")) if lead.get("assigned_to") else None
                    lead_copy["creator_user"] = self.store.get_profile(lead.get("created_by")) if lead.get("created_by") else None
                    lead_copy["activities_count"] = sum(1 for a in self.store.activities if str(a.get("lead_id")) == str(lead.get("id")))
                    lead_copy["tasks_count"] = sum(1 for t in self.store.tasks if str(t.get("lead_id")) == str(lead.get("id")))
                    return lead_copy
            return None

    async def create_lead(self, lead_data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        if self.supabase:
            try:
                lead_id = str(uuid.uuid4())
                now = datetime.now(timezone.utc).isoformat()
                
                record = {
                    "id": lead_id,
                    "company_name": lead_data["company_name"].strip(),
                    "contact_name": lead_data.get("contact_name") or None,
                    "job_title": lead_data.get("job_title") or None,
                    "email": lead_data.get("email") or None,
                    "phone": lead_data.get("phone") or None,
                    "website": lead_data.get("website") or None,
                    "industry": lead_data.get("industry") or None,
                    "country": lead_data.get("country") or None,
                    "source": lead_data.get("source") or "Upwork",
                    "custom_source": lead_data.get("custom_source") or None,
                    "project_title": lead_data.get("project_title") or None,
                    "project_description": lead_data.get("project_description") or None,
                    "budget": float(lead_data.get("budget", 0.0) or 0.0),
                    "currency": lead_data.get("currency") or "USD",
                    "expected_deadline": str(lead_data.get("expected_deadline")) if lead_data.get("expected_deadline") else None,
                    "priority": lead_data.get("priority") or "MEDIUM",
                    "status": lead_data.get("status") or "NEW",
                    "assigned_to": lead_data.get("assigned_to") or None,
                    "follow_up_date": lead_data.get("follow_up_date") or None,
                    "verification_status": "UNVERIFIED",
                    "verification_score": 0,
                    "verification_details": None,
                    "last_verified_at": None,
                    "is_candidate": bool(lead_data.get("is_candidate", False)),
                    "source_record_id": lead_data.get("source_record_id") or None,
                    "normalized_email": lead_data.get("normalized_email") or None,
                    "normalized_phone": lead_data.get("normalized_phone") or None,
                    "normalized_company": lead_data.get("normalized_company") or None,
                    "created_by": str(current_user.get("id")),
                    "created_at": now,
                    "updated_at": now
                }
                
                try:
                    self.supabase.table("leads").insert(_serialize_for_db(record)).execute()
                except Exception as insert_err:
                    err_msg = str(insert_err).lower()
                    if "foreign key" in err_msg and "created_by" in err_msg:
                        record["created_by"] = None
                        self.supabase.table("leads").insert(_serialize_for_db(record)).execute()
                    else:
                        print(f"[DB] Error in create_lead insert: {insert_err}")
                        if "column" in err_msg or "does not exist" in err_msg or "schema" in err_msg:
                            raise RuntimeError(
                                f"Database schema mismatch: required columns are missing in Supabase leads table. "
                                f"Run backend/migrations/03_verification_system_upgrade.sql in Supabase SQL Editor. Error: {insert_err}"
                            ) from insert_err
                        raise insert_err
                
                initial_activity = {
                    "lead_id": lead_id,
                    "user_id": str(current_user.get("id")),
                    "type": "Status Change",
                    "title": "Lead created",
                    "description": f"Lead registered from {record['source']}. Initial status set to {record['status']}.",
                    "next_action": "Review lead & schedule initial contact",
                    "activity_date": now,
                    "follow_up_date": record.get("follow_up_date") or None,
                }
                try:
                    self.supabase.table("activities").insert(initial_activity).execute()
                except Exception as act_err:
                    if "foreign key" in str(act_err).lower() or "user_id" in str(act_err).lower():
                        initial_activity["user_id"] = None
                        try:
                            self.supabase.table("activities").insert(initial_activity).execute()
                        except Exception:
                            pass
                
                status_entry = {
                    "lead_id": lead_id,
                    "old_status": None,
                    "new_status": record["status"],
                    "changed_by": str(current_user.get("id")),
                }
                try:
                    self.supabase.table("status_history").insert(status_entry).execute()
                except Exception as sh_err:
                    if "foreign key" in str(sh_err).lower() or "changed_by" in str(sh_err).lower():
                        status_entry["changed_by"] = None
                        try:
                            self.supabase.table("status_history").insert(status_entry).execute()
                        except Exception:
                            pass
                
                return await self.get_lead(lead_id, current_user)
            except Exception as e:
                print(f"[DB] Error in create_lead: {e}")
                raise e

        else:
            new_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            
            record = {
                "id": new_id,
                "company_name": lead_data["company_name"].strip(),
                "contact_name": lead_data.get("contact_name"),
                "email": lead_data.get("email"),
                "phone": lead_data.get("phone"),
                "website": lead_data.get("website"),
                "industry": lead_data.get("industry"),
                "country": lead_data.get("country"),
                "source": lead_data.get("source", "Upwork"),
                "custom_source": lead_data.get("custom_source"),
                "project_title": lead_data.get("project_title"),
                "project_description": lead_data.get("project_description"),
                "budget": float(lead_data.get("budget", 0.0) or 0.0),
                "currency": lead_data.get("currency", "USD"),
                "expected_deadline": lead_data.get("expected_deadline"),
                "priority": lead_data.get("priority", "MEDIUM"),
                "status": lead_data.get("status", "NEW"),
                "assigned_to": lead_data.get("assigned_to"),
                "follow_up_date": lead_data.get("follow_up_date"),
                "lead_score": None,
                "lead_score_label": None,
                "ai_summary": None,
                "ai_analysis": None,
                "verification_status": "UNVERIFIED",
                "verification_score": 0,
                "verification_details": None,
                "last_verified_at": None,
                "is_candidate": False,
                "source_record_id": None,
                "normalized_email": None,
                "normalized_phone": None,
                "normalized_company": None,
                "created_by": str(current_user.get("id")),
                "created_at": now,
                "updated_at": now
            }
            self.store.leads.insert(0, record)
            
            initial_activity = {
                "id": str(uuid.uuid4()),
                "lead_id": new_id,
                "user_id": str(current_user.get("id")),
                "type": "Status Change",
                "title": "Lead created",
                "description": f"Lead registered from {record['source']}. Initial status set to {record['status']}.",
                "next_action": "Review lead & schedule initial contact",
                "activity_date": now,
                "follow_up_date": record.get("follow_up_date") or None,
                "created_at": now
            }
            self.store.activities.insert(0, initial_activity)

            status_entry = {
                "id": str(uuid.uuid4()),
                "lead_id": new_id,
                "old_status": None,
                "new_status": record["status"],
                "changed_by": str(current_user.get("id")),
                "changed_at": now
            }
            self.store.status_history.insert(0, status_entry)

            return await self.get_lead(new_id, current_user)

    async def create_leads_bulk(
        self,
        leads_data: List[Dict[str, Any]],
        current_user: Dict[str, Any],
        batch_size: int = 200
    ) -> List[Dict[str, Any]]:
        if not leads_data:
            return []

        user_id = str(current_user.get("id")) if current_user and current_user.get("id") else None
        now = datetime.now(timezone.utc).isoformat()

        prepared_records = []
        for lead_data in leads_data:
            lead_id = lead_data.get("id") or str(uuid.uuid4())
            record = {
                "id": lead_id,
                "company_name": (lead_data.get("company_name") or "").strip(),
                "contact_name": lead_data.get("contact_name") or None,
                "job_title": lead_data.get("job_title") or None,
                "email": lead_data.get("email") or None,
                "phone": lead_data.get("phone") or None,
                "website": lead_data.get("website") or None,
                "industry": lead_data.get("industry") or None,
                "country": lead_data.get("country") or None,
                "source": lead_data.get("source") or "CSV Import",
                "custom_source": lead_data.get("custom_source") or None,
                "project_title": lead_data.get("project_title") or None,
                "project_description": lead_data.get("project_description") or None,
                "budget": float(lead_data.get("budget", 0.0) or 0.0),
                "currency": lead_data.get("currency") or "USD",
                "expected_deadline": str(lead_data.get("expected_deadline")) if lead_data.get("expected_deadline") else None,
                "priority": lead_data.get("priority") or "MEDIUM",
                "status": lead_data.get("status") or "NEW",
                "assigned_to": lead_data.get("assigned_to") or None,
                "follow_up_date": lead_data.get("follow_up_date") or None,
                "verification_status": lead_data.get("verification_status") or "UNVERIFIED",
                "verification_score": int(lead_data.get("verification_score") or 0),
                "verification_details": lead_data.get("verification_details") or None,
                "last_verified_at": lead_data.get("last_verified_at") or None,
                "is_candidate": bool(lead_data.get("is_candidate", False)),
                "source_record_id": lead_data.get("source_record_id") or None,
                "normalized_email": lead_data.get("normalized_email") or None,
                "normalized_phone": lead_data.get("normalized_phone") or None,
                "normalized_company": lead_data.get("normalized_company") or None,
                "created_by": user_id,
                "created_at": now,
                "updated_at": now
            }
            prepared_records.append(record)

        if self.supabase:
            created_leads = []
            for i in range(0, len(prepared_records), batch_size):
                chunk = prepared_records[i : i + batch_size]
                serialized_chunk = [_serialize_for_db(r) for r in chunk]
                try:
                    res = self.supabase.table("leads").insert(serialized_chunk).execute()
                    if res.data:
                        for row in res.data:
                            created_leads.append(_format_lead_out(row))
                    else:
                        for r in chunk:
                            created_leads.append(_format_lead_out(r))
                except Exception as insert_err:
                    err_msg = str(insert_err).lower()
                    if "foreign key" in err_msg and "created_by" in err_msg:
                        for r in serialized_chunk:
                            r["created_by"] = None
                        res = self.supabase.table("leads").insert(serialized_chunk).execute()
                        if res.data:
                            for row in res.data:
                                created_leads.append(_format_lead_out(row))
                        else:
                            for r in chunk:
                                created_leads.append(_format_lead_out(r))
                    else:
                        print(f"[DB] Bulk insert FAILED: {insert_err}")
                        if "column" in err_msg or "does not exist" in err_msg or "schema" in err_msg:
                            raise RuntimeError(
                                f"Database schema mismatch: required verification columns are missing in Supabase leads table. "
                                f"Run backend/migrations/03_verification_system_upgrade.sql in your Supabase SQL Editor. Error: {insert_err}"
                            ) from insert_err
                        raise insert_err
            return created_leads
        else:
            for r in prepared_records:
                self.store.leads.insert(0, dict(r))
            return [_format_lead_out(r) for r in prepared_records]


    async def update_lead(self, lead_id: str, updates: Dict[str, Any], current_user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.supabase:
            try:
                existing = await self.get_lead(lead_id, current_user)
                if not existing:
                    return None
                
                old_status = existing.get("status")
                new_status = updates.get("status")
                user_id = str(current_user.get("id"))
                now = datetime.now(timezone.utc).isoformat()
                
                if new_status and new_status != old_status:
                    history_entry = {
                        "lead_id": lead_id,
                        "old_status": old_status,
                        "new_status": new_status,
                        "changed_by": user_id,
                    }
                    self.supabase.table("status_history").insert(history_entry).execute()
                    
                    activity_entry = {
                        "lead_id": lead_id,
                        "user_id": user_id,
                        "type": "Status Change",
                        "title": f"Status changed to {new_status}",
                        "description": f"Lead status updated from {old_status} to {new_status}.",
                        "outcome": updates.get("notes") or None,
                        "activity_date": now,
                    }
                    self.supabase.table("activities").insert(activity_entry).execute()
                
                formatted_updates = {}
                for k, v in updates.items():
                    if k == "expected_deadline" and v:
                        formatted_updates[k] = str(v)
                    elif k != "notes":
                        formatted_updates[k] = v

                self.supabase.table("leads").update(_serialize_for_db(formatted_updates)).eq("id", lead_id).execute()
                return await self.get_lead(lead_id, current_user)
            except Exception as e:
                print(f"[DB] Error in update_lead: {e}")
                raise e
        else:
            is_admin = current_user.get("role") == "admin"
            user_id = str(current_user.get("id"))
            now = datetime.now(timezone.utc).isoformat()

            for lead in self.store.leads:
                if str(lead.get("id")) == str(lead_id):
                    if not is_admin:
                        lead_assigned = str(lead.get("assigned_to") or "")
                        lead_creator = str(lead.get("created_by") or "")
                        if lead_assigned != user_id and lead_creator != user_id:
                            return None
                    
                    old_status = lead.get("status")
                    new_status = updates.get("status")

                    if new_status and new_status != old_status:
                        history_entry = {
                            "id": str(uuid.uuid4()),
                            "lead_id": lead_id,
                            "old_status": old_status,
                            "new_status": new_status,
                            "changed_by": user_id,
                            "changed_at": now
                        }
                        self.store.status_history.insert(0, history_entry)

                        activity_entry = {
                            "id": str(uuid.uuid4()),
                            "lead_id": lead_id,
                            "user_id": user_id,
                            "type": "Status Change",
                            "title": f"Status changed to {new_status}",
                            "description": f"Lead status updated from {old_status} to {new_status}.",
                            "outcome": updates.get("notes") or None,
                            "next_action": None,
                            "activity_date": now,
                            "follow_up_date": None,
                            "created_at": now
                        }
                        self.store.activities.insert(0, activity_entry)

                    for k, v in updates.items():
                        if v is not None:
                            if k == "expected_deadline":
                                lead[k] = str(v)
                            else:
                                lead[k] = v
                    lead["updated_at"] = now
                    return await self.get_lead(lead_id, current_user)
            return None

    async def delete_lead(self, lead_id: str, current_user: Dict[str, Any]) -> bool:
        if self.supabase:
            try:
                if current_user.get("role") != "admin":
                    return False
                self.supabase.table("leads").delete().eq("id", lead_id).execute()
                return True
            except Exception as e:
                print(f"[DB] Error in delete_lead: {e}")
                raise e
        else:
            if current_user.get("role") != "admin":
                return False
            
            for i, lead in enumerate(self.store.leads):
                if str(lead.get("id")) == str(lead_id):
                    self.store.leads.pop(i)
                    self.store.activities = [a for a in self.store.activities if str(a.get("lead_id")) != str(lead_id)]
                    self.store.tasks = [t for t in self.store.tasks if str(t.get("lead_id")) != str(lead_id)]
                    self.store.proposals = [p for p in self.store.proposals if str(p.get("lead_id")) != str(lead_id)]
                    self.store.status_history = [s for s in self.store.status_history if str(s.get("lead_id")) != str(lead_id)]
                    self.store.ai_analyses = [x for x in self.store.ai_analyses if str(x.get("lead_id")) != str(lead_id)]
                    return True
            return False

    # --- Activities ---
    async def get_raw_activities(self) -> List[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("activities").select("*").order("activity_date", desc=True).execute()
                return res.data or []
            except Exception as e:
                print(f"[DB] Error in get_raw_activities: {e}")
                raise e
        return self.store.activities

    async def list_activities_for_lead(self, lead_id: str) -> List[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("activities").select("*").eq("lead_id", lead_id).order("activity_date", desc=True).execute()
                acts = res.data or []
                all_profiles = {p["id"]: p for p in await self.list_profiles()}
                for a in acts:
                    a["user"] = all_profiles.get(a.get("user_id")) if a.get("user_id") else None
                return acts
            except Exception as e:
                print(f"[DB] Error in list_activities_for_lead: {e}")
                raise e
        else:
            acts = [dict(a) for a in self.store.activities if str(a.get("lead_id")) == str(lead_id)]
            for a in acts:
                a["user"] = self.store.get_profile(a.get("user_id")) if a.get("user_id") else None
            acts.sort(key=lambda x: x.get("activity_date", ""), reverse=True)
            return acts

    async def create_activity(self, lead_id: str, act_data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        if self.supabase:
            try:
                now = datetime.now(timezone.utc).isoformat()
                act_date = str(act_data.get("activity_date") or now)
                f_date = str(act_data.get("follow_up_date")) if act_data.get("follow_up_date") else None
                
                record = {
                    "lead_id": lead_id,
                    "user_id": str(current_user.get("id")),
                    "type": act_data["type"],
                    "title": act_data["title"],
                    "description": act_data.get("description") or None,
                    "outcome": act_data.get("outcome") or None,
                    "next_action": act_data.get("next_action") or None,
                    "activity_date": act_date,
                    "follow_up_date": f_date or None,
                }
                res = self.supabase.table("activities").insert(record).execute()
                created = res.data[0]
                
                if f_date:
                    self.supabase.table("leads").update({"follow_up_date": f_date}).eq("id", lead_id).execute()
                
                all_profiles = {p["id"]: p for p in await self.list_profiles()}
                created["user"] = all_profiles.get(created.get("user_id"))
                return created
            except Exception as e:
                print(f"[DB] Error in create_activity: {e}")
                raise e
        else:
            now = datetime.now(timezone.utc).isoformat()
            new_id = str(uuid.uuid4())
            act_date = str(act_data.get("activity_date") or now)
            f_date = str(act_data.get("follow_up_date")) if act_data.get("follow_up_date") else None

            activity = {
                "id": new_id,
                "lead_id": lead_id,
                "user_id": str(current_user.get("id")),
                "type": act_data["type"],
                "title": act_data["title"],
                "description": act_data.get("description"),
                "outcome": act_data.get("outcome"),
                "next_action": act_data.get("next_action"),
                "activity_date": act_date,
                "follow_up_date": f_date,
                "created_at": now
            }
            self.store.activities.insert(0, activity)

            if f_date:
                for lead in self.store.leads:
                    if str(lead.get("id")) == str(lead_id):
                        lead["follow_up_date"] = f_date
                        lead["updated_at"] = now
                        break

            act_copy = dict(activity)
            act_copy["user"] = self.store.get_profile(current_user.get("id"))
            return act_copy

    # --- Tasks ---
    async def list_tasks(self, current_user: Dict[str, Any], lead_id: Optional[str] = None,
                          assigned_to: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.supabase:
            try:
                query = self.supabase.table("tasks").select("*")
                if current_user.get("role") != "admin":
                    user_id = str(current_user.get("id"))
                    query = query.or_(f"assigned_to.eq.{user_id},created_by.eq.{user_id}")
                
                if lead_id:
                    query = query.eq("lead_id", lead_id)
                if assigned_to:
                    query = query.eq("assigned_to", assigned_to)
                if status:
                    query = query.eq("status", status)
                
                res = query.order("due_date", nullsfirst=False).execute()
                tasks = res.data or []
                
                all_profiles = {p["id"]: p for p in await self.list_profiles()}
                
                leads_res = self.supabase.table("leads").select("id", "company_name", "project_title").execute()
                leads_map = {l["id"]: l for l in (leads_res.data or [])}
                
                for t in tasks:
                    t["assigned_user"] = all_profiles.get(t.get("assigned_to")) if t.get("assigned_to") else None
                    if t.get("lead_id") and t.get("lead_id") in leads_map:
                        t["lead_company_name"] = leads_map[t["lead_id"]].get("company_name")
                        t["lead_project_title"] = leads_map[t["lead_id"]].get("project_title")
                return tasks
            except Exception as e:
                print(f"[DB] Error in list_tasks: {e}")
                raise e
        else:
            is_admin = current_user.get("role") == "admin"
            user_id = str(current_user.get("id"))
            
            results = []
            for task in self.store.tasks:
                if not is_admin:
                    task_assigned = str(task.get("assigned_to") or "")
                    task_creator = str(task.get("created_by") or "")
                    if task_assigned != user_id and task_creator != user_id:
                        continue

                if lead_id and str(task.get("lead_id") or "") != str(lead_id):
                    continue
                if assigned_to and str(task.get("assigned_to") or "") != str(assigned_to):
                    continue
                if status and task.get("status") != status:
                    continue

                t_copy = dict(task)
                t_copy["assigned_user"] = self.store.get_profile(task.get("assigned_to")) if task.get("assigned_to") else None
                if task.get("lead_id"):
                    for lead in self.store.leads:
                        if str(lead.get("id")) == str(task.get("lead_id")):
                            t_copy["lead_company_name"] = lead.get("company_name")
                            t_copy["lead_project_title"] = lead.get("project_title")
                            break
                results.append(t_copy)

            results.sort(key=lambda x: x.get("due_date") or "9999", reverse=False)
            return results

    async def create_task(self, task_data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        if self.supabase:
            try:
                now = datetime.now(timezone.utc).isoformat()
                due = str(task_data.get("due_date")) if task_data.get("due_date") else None
                record = {
                    "lead_id": task_data.get("lead_id") or None,
                    "assigned_to": task_data.get("assigned_to") or str(current_user.get("id")),
                    "title": task_data["title"],
                    "description": task_data.get("description") or None,
                    "priority": task_data.get("priority") or "MEDIUM",
                    "status": task_data.get("status") or "PENDING",
                    "due_date": due or None,
                    "created_by": str(current_user.get("id")),
                    "created_at": now,
                    "updated_at": now
                }
                res = self.supabase.table("tasks").insert(record).execute()
                created = res.data[0]
                
                all_profiles = {p["id"]: p for p in await self.list_profiles()}
                created["assigned_user"] = all_profiles.get(created.get("assigned_to"))
                
                if created.get("lead_id"):
                    lead_res = self.supabase.table("leads").select("company_name", "project_title").eq("id", created["lead_id"]).execute()
                    if lead_res.data:
                        created["lead_company_name"] = lead_res.data[0].get("company_name")
                        created["lead_project_title"] = lead_res.data[0].get("project_title")
                return created
            except Exception as e:
                print(f"[DB] Error in create_task: {e}")
                raise e
        else:
            now = datetime.now(timezone.utc).isoformat()
            new_id = str(uuid.uuid4())
            due = str(task_data.get("due_date")) if task_data.get("due_date") else None
            
            task = {
                "id": new_id,
                "lead_id": task_data.get("lead_id"),
                "assigned_to": task_data.get("assigned_to") or str(current_user.get("id")),
                "title": task_data["title"],
                "description": task_data.get("description"),
                "priority": task_data.get("priority", "MEDIUM"),
                "status": task_data.get("status", "PENDING"),
                "due_date": due,
                "created_by": str(current_user.get("id")),
                "created_at": now,
                "updated_at": now
            }
            self.store.tasks.insert(0, task)
            
            t_copy = dict(task)
            t_copy["assigned_user"] = self.store.get_profile(task.get("assigned_to"))
            if task.get("lead_id"):
                for lead in self.store.leads:
                    if str(lead.get("id")) == str(task.get("lead_id")):
                        t_copy["lead_company_name"] = lead.get("company_name")
                        t_copy["lead_project_title"] = lead.get("project_title")
                        break
            return t_copy

    async def update_task(self, task_id: str, updates: Dict[str, Any], current_user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.supabase:
            try:
                cleaned = {}
                for k, v in updates.items():
                    if k == "due_date" and v:
                        cleaned[k] = str(v)
                    else:
                        cleaned[k] = v
                cleaned["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                res = self.supabase.table("tasks").update(cleaned).eq("id", task_id).execute()
                if not res.data:
                    return None
                
                created = res.data[0]
                all_profiles = {p["id"]: p for p in await self.list_profiles()}
                created["assigned_user"] = all_profiles.get(created.get("assigned_to"))
                
                if created.get("lead_id"):
                    lead_res = self.supabase.table("leads").select("company_name", "project_title").eq("id", created["lead_id"]).execute()
                    if lead_res.data:
                        created["lead_company_name"] = lead_res.data[0].get("company_name")
                        created["lead_project_title"] = lead_res.data[0].get("project_title")
                return created
            except Exception as e:
                print(f"[DB] Error in update_task: {e}")
                raise e
        else:
            is_admin = current_user.get("role") == "admin"
            user_id = str(current_user.get("id"))
            now = datetime.now(timezone.utc).isoformat()

            for task in self.store.tasks:
                if str(task.get("id")) == str(task_id):
                    if not is_admin:
                        task_assigned = str(task.get("assigned_to") or "")
                        task_creator = str(task.get("created_by") or "")
                        if task_assigned != user_id and task_creator != user_id:
                            return None
                    
                    for k, v in updates.items():
                        if v is not None:
                            task[k] = str(v) if k == "due_date" else v
                    task["updated_at"] = now

                    t_copy = dict(task)
                    t_copy["assigned_user"] = self.store.get_profile(task.get("assigned_to"))
                    if task.get("lead_id"):
                        for lead in self.store.leads:
                            if str(lead.get("id")) == str(task.get("lead_id")):
                                t_copy["lead_company_name"] = lead.get("company_name")
                                t_copy["lead_project_title"] = lead.get("project_title")
                                break
                    return t_copy
            return None

    async def delete_task(self, task_id: str, current_user: Dict[str, Any]) -> bool:
        if self.supabase:
            try:
                self.supabase.table("tasks").delete().eq("id", task_id).execute()
                return True
            except Exception as e:
                print(f"[DB] Error in delete_task: {e}")
                raise e
        else:
            is_admin = current_user.get("role") == "admin"
            user_id = str(current_user.get("id"))

            for i, task in enumerate(self.store.tasks):
                if str(task.get("id")) == str(task_id):
                    if not is_admin:
                        task_assigned = str(task.get("assigned_to") or "")
                        task_creator = str(task.get("created_by") or "")
                        if task_assigned != user_id and task_creator != user_id:
                            return False
                    self.store.tasks.pop(i)
                    return True
            return False

    # --- Status History ---
    async def list_status_history(self, lead_id: str) -> List[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("status_history").select("*").eq("lead_id", lead_id).order("changed_at", desc=True).execute()
                history = res.data or []
                all_profiles = {p["id"]: p for p in await self.list_profiles()}
                for h in history:
                    h["changed_by_user"] = all_profiles.get(h.get("changed_by")) if h.get("changed_by") else None
                return history
            except Exception as e:
                print(f"[DB] Error in list_status_history: {e}")
                raise e
        else:
            history = [dict(s) for s in self.store.status_history if str(s.get("lead_id")) == str(lead_id)]
            for h in history:
                h["changed_by_user"] = self.store.get_profile(h.get("changed_by")) if h.get("changed_by") else None
            history.sort(key=lambda x: x.get("changed_at", ""), reverse=True)
            return history

    # --- Proposals ---
    async def list_proposals_for_lead(self, lead_id: str) -> List[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("proposals").select("*").eq("lead_id", lead_id).order("created_at", desc=True).execute()
                props = res.data or []
                all_profiles = {p["id"]: p for p in await self.list_profiles()}
                for p in props:
                    p["creator_user"] = all_profiles.get(p.get("created_by")) if p.get("created_by") else None
                return props
            except Exception as e:
                print(f"[DB] Error in list_proposals_for_lead: {e}")
                raise e
        else:
            props = [dict(p) for p in self.store.proposals if str(p.get("lead_id")) == str(lead_id)]
            for p in props:
                p["creator_user"] = self.store.get_profile(p.get("created_by")) if p.get("created_by") else None
            props.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return props

    async def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("proposals").select("*").eq("id", proposal_id).execute()
                if not res.data:
                    return None
                proposal = res.data[0]
                all_profiles = {p["id"]: p for p in await self.list_profiles()}
                proposal["creator_user"] = all_profiles.get(proposal.get("created_by")) if proposal.get("created_by") else None
                return proposal
            except Exception as e:
                print(f"[DB] Error in get_proposal: {e}")
                raise e
        else:
            for p in self.store.proposals:
                if str(p.get("id")) == str(proposal_id):
                    p_copy = dict(p)
                    p_copy["creator_user"] = self.store.get_profile(p.get("created_by")) if p.get("created_by") else None
                    return p_copy
            return None

    async def save_proposal(self, lead_id: str, title: str, content: Dict[str, Any],
                             status: str, current_user: Dict[str, Any]) -> Dict[str, Any]:
        if self.supabase:
            try:
                now = datetime.now(timezone.utc).isoformat()
                record = {
                    "lead_id": lead_id,
                    "created_by": str(current_user.get("id")),
                    "title": title,
                    "content": content,
                    "status": status,
                    "created_at": now,
                    "updated_at": now
                }
                res = self.supabase.table("proposals").insert(record).execute()
                return res.data[0]
            except Exception as e:
                print(f"[DB] Error in save_proposal: {e}")
                raise e
        else:
            now = datetime.now(timezone.utc).isoformat()
            new_id = str(uuid.uuid4())
            proposal = {
                "id": new_id,
                "lead_id": lead_id,
                "created_by": str(current_user.get("id")),
                "title": title,
                "content": content,
                "status": status,
                "created_at": now,
                "updated_at": now
            }
            self.store.proposals.insert(0, proposal)
            return proposal

    async def update_proposal(self, proposal_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.supabase:
            try:
                cleaned = dict(updates)
                cleaned["updated_at"] = datetime.now(timezone.utc).isoformat()
                res = self.supabase.table("proposals").update(cleaned).eq("id", proposal_id).execute()
                if res.data:
                    return await self.get_proposal(proposal_id)
                return None
            except Exception as e:
                print(f"[DB] Error in update_proposal: {e}")
                raise e
        else:
            now = datetime.now(timezone.utc).isoformat()
            for p in self.store.proposals:
                if str(p.get("id")) == str(proposal_id):
                    for k, v in updates.items():
                        if v is not None:
                            p[k] = v
                    p["updated_at"] = now
                    return await self.get_proposal(proposal_id)
            return None

    # --- AI Analyses ---
    async def list_ai_analyses_for_lead(self, lead_id: str) -> List[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("ai_analyses").select("*").eq("lead_id", lead_id).order("created_at", desc=True).execute()
                return res.data or []
            except Exception as e:
                print(f"[DB] Error in list_ai_analyses_for_lead: {e}")
                raise e
        else:
            return [x for x in self.store.ai_analyses if str(x.get("lead_id")) == str(lead_id)]

    async def create_ai_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(analysis)
        if "id" not in record or not record["id"]:
            record["id"] = str(uuid.uuid4())
        if "created_at" not in record or not record["created_at"]:
            record["created_at"] = datetime.now(timezone.utc).isoformat()

        if self.supabase:
            try:
                res = self.supabase.table("ai_analyses").insert(record).execute()
                return res.data[0]
            except Exception as e:
                print(f"[DB] Error in create_ai_analysis: {e}")
                raise e
        else:
            self.store.ai_analyses.insert(0, record)
            return record

    # --- Lead Discovery & Verification ---
    async def discover_leads(
        self,
        current_user: Dict[str, Any],
        query: Optional[str] = None,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        job_title: Optional[str] = None,
        verification_status: Optional[str] = None,
        min_verification_score: Optional[int] = None,
        is_candidate: Optional[bool] = None,
        source: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        if self.supabase:
            try:
                # Select all leads — candidates and verified directory items are company-wide discovery assets
                q = self.supabase.table("leads").select("*")

                res = q.order("created_at", desc=True).execute()
                all_raw = res.data or []
                
                # Format each lead with discovery extraction
                all_leads = [_format_lead_out(lead) for lead in all_raw]

                # Filter in Python for robust handling across both native and embedded fields
                filtered = []
                for lead in all_leads:
                    if country and country.lower() not in (lead.get("country") or "").lower():
                        continue
                    if industry and industry.lower() not in (lead.get("industry") or "").lower():
                        continue
                    if job_title and job_title.lower() not in (lead.get("job_title") or "").lower():
                        continue
                    if verification_status and lead.get("verification_status") != verification_status:
                        continue
                    if min_verification_score is not None and (lead.get("verification_score") or 0) < min_verification_score:
                        continue
                    if is_candidate is not None and bool(lead.get("is_candidate")) != is_candidate:
                        continue
                    if source and source.lower() not in (lead.get("source") or "").lower():
                        continue
                    if query:
                        s = query.lower().strip()
                        match = (
                            s in (lead.get("company_name") or "").lower() or
                            s in (lead.get("contact_name") or "").lower() or
                            s in (lead.get("email") or "").lower() or
                            s in (lead.get("job_title") or "").lower() or
                            s in (lead.get("industry") or "").lower() or
                            s in (lead.get("country") or "").lower()
                        )
                        if not match:
                            continue
                    filtered.append(lead)

                total = len(filtered)
                offset = (page - 1) * page_size
                paginated = filtered[offset: offset + page_size]

                all_profiles = {p["id"]: p for p in await self.list_profiles()}
                for lead in paginated:
                    lead["assigned_user"] = all_profiles.get(lead.get("assigned_to")) if lead.get("assigned_to") else None
                    lead["creator_user"] = all_profiles.get(lead.get("created_by")) if lead.get("created_by") else None
                    lead["activities_count"] = 0
                    lead["tasks_count"] = 0

                total_pages = max(1, (total + page_size - 1) // page_size)
                return {"leads": paginated, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages}
            except Exception as e:
                print(f"[DB] Error in discover_leads: {e}")
                raise e
        else:
            # Memory store search
            all_leads = [_format_lead_out(lead) for lead in self.store.leads]
            filtered = []
            for lead in all_leads:
                if country and country.lower() not in (lead.get("country") or "").lower():
                    continue
                if industry and industry.lower() not in (lead.get("industry") or "").lower():
                    continue
                if job_title and job_title.lower() not in (lead.get("job_title") or "").lower():
                    continue
                if verification_status and lead.get("verification_status") != verification_status:
                    continue
                if min_verification_score is not None and (lead.get("verification_score") or 0) < min_verification_score:
                    continue
                if is_candidate is not None and bool(lead.get("is_candidate")) != is_candidate:
                    continue
                if source and source.lower() not in (lead.get("source") or "").lower():
                    continue
                if query:
                    s = query.lower().strip()
                    match = (
                        s in (lead.get("company_name") or "").lower() or
                        s in (lead.get("contact_name") or "").lower() or
                        s in (lead.get("email") or "").lower() or
                        s in (lead.get("job_title") or "").lower() or
                        s in (lead.get("industry") or "").lower() or
                        s in (lead.get("country") or "").lower()
                    )
                    if not match:
                        continue
                filtered.append(lead)

            total = len(filtered)
            offset = (page - 1) * page_size
            paginated = filtered[offset: offset + page_size]
            total_pages = max(1, (total + page_size - 1) // page_size)
            return {"leads": paginated, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages}

    async def update_lead_verification(self, lead_id: str, verification_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update lead with verification results from LeadVerificationEngine.verify_lead()"""
        if self.supabase:
            try:
                now_iso = datetime.now(timezone.utc).isoformat()
                updates = {
                    "verification_status": verification_result.get("verification_status", "UNVERIFIED"),
                    "verification_score": int(verification_result.get("verification_score", 0)),
                    "verification_details": verification_result.get("verification_details"),
                    "last_verified_at": verification_result.get("last_verified_at") or now_iso,
                    "updated_at": now_iso
                }
                self.supabase.table("leads").update(updates).eq("id", lead_id).execute()
                
                res = self.supabase.table("leads").select("*").eq("id", lead_id).execute()
                if res.data:
                    lead = _format_lead_out(res.data[0])
                    lead["assigned_user"] = None
                    lead["creator_user"] = None
                    lead["activities_count"] = 0
                    lead["tasks_count"] = 0
                    return lead
            except Exception as e:
                print(f"[DB] Error in update_lead_verification: {e}")
                err_msg = str(e).lower()
                if "column" in err_msg or "does not exist" in err_msg or "schema" in err_msg:
                    raise RuntimeError(
                        f"Database schema mismatch: verification columns are missing in Supabase leads table. "
                        f"Run backend/migrations/03_verification_system_upgrade.sql in your Supabase SQL Editor. Error: {e}"
                    ) from e
                raise e
        else:
            for l in self.store.leads:
                if str(l.get("id")) == str(lead_id):
                    l["verification_status"] = verification_result.get("verification_status", "UNVERIFIED")
                    l["verification_score"] = verification_result.get("verification_score", 0)
                    l["verification_details"] = verification_result.get("verification_details")
                    l["last_verified_at"] = verification_result.get("last_verified_at") or datetime.now(timezone.utc).isoformat()
                    l["updated_at"] = datetime.now(timezone.utc).isoformat()
                    return _format_lead_out(l)
            return None
        return None

    async def promote_candidate_to_crm(self, lead_id: str, current_user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Remove candidate flag so lead becomes a full CRM lead"""
        if self.supabase:
            try:
                now_iso = datetime.now(timezone.utc).isoformat()
                updates = {
                    "is_candidate": False,
                    "assigned_to": str(current_user.get("id")),
                    "status": "NEW",
                    "updated_at": now_iso
                }
                self.supabase.table("leads").update(updates).eq("id", lead_id).execute()
                return await self.get_lead(lead_id, current_user)
            except Exception as e:
                print(f"[DB] Error in promote_candidate_to_crm: {e}")
                err_msg = str(e).lower()
                if "column" in err_msg or "does not exist" in err_msg or "schema" in err_msg:
                    raise RuntimeError(
                        f"Database schema mismatch: is_candidate column is missing in Supabase leads table. "
                        f"Run backend/migrations/03_verification_system_upgrade.sql in your Supabase SQL Editor. Error: {e}"
                    ) from e
                raise e
        else:
            for l in self.store.leads:
                if str(l.get("id")) == str(lead_id):
                    l["is_candidate"] = False
                    l["assigned_to"] = str(current_user.get("id"))
                    l["status"] = "NEW"
                    l["updated_at"] = datetime.now(timezone.utc).isoformat()
                    return await self.get_lead(lead_id, current_user)
            return None
        return None

    async def create_lead_import_record(self, import_data: Dict[str, Any]) -> Dict[str, Any]:
        record = {
            "id": str(uuid.uuid4()),
            "file_name": import_data.get("file_name", ""),
            "total_rows": import_data.get("total_rows", 0),
            "valid_rows": import_data.get("valid_rows", 0),
            "invalid_rows": import_data.get("invalid_rows", 0),
            "duplicate_rows": import_data.get("duplicate_rows", 0),
            "verified_rows": import_data.get("verified_rows", 0),
            "unverified_rows": import_data.get("unverified_rows", 0),
            "accepted_rows": import_data.get("accepted_rows", 0),
            "rejected_rows": import_data.get("rejected_rows", 0),
            "rejection_threshold": import_data.get("rejection_threshold", 70),
            "created_by": import_data.get("created_by"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        if self.supabase:
            try:
                res = self.supabase.table("lead_imports").insert(record).execute()
                return res.data[0] if res.data else record
            except Exception as e:
                print(f"[DB] Lead imports table notice: {e}")
                return record
        return record

    async def list_lead_imports(self, current_user: Dict[str, Any]) -> List[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("lead_imports").select("*").order("created_at", desc=True).execute()
                return res.data or []
            except Exception as e:
                print(f"[DB] list_lead_imports: {e}")
                return []
        return []

    # --- Teams & Team Members ---
    async def list_teams(self) -> List[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("teams").select("*").order("name").execute()
                return res.data or []
            except Exception as e:
                print(f"[DB] Error in list_teams: {e}")
                if "PGRST205" in str(e):
                    return self.store.list_teams()
                raise e
        return self.store.list_teams()

    async def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("teams").select("*").eq("id", team_id).execute()
                if res.data:
                    return res.data[0]
                return None
            except Exception as e:
                print(f"[DB] Error in get_team: {e}")
                if "PGRST205" in str(e):
                    return self.store.get_team(team_id)
                raise e
        return self.store.get_team(team_id)

    async def get_team_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("teams").select("*").ilike("name", name.strip()).execute()
                if res.data:
                    return res.data[0]
                return None
            except Exception as e:
                print(f"[DB] Error in get_team_by_name: {e}")
                if "PGRST205" in str(e):
                    return self.store.get_team_by_name(name)
                raise e
        return self.store.get_team_by_name(name)

    async def create_team(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        if self.supabase:
            try:
                record = {
                    "name": name.strip(),
                    "description": description.strip() if description else None
                }
                res = self.supabase.table("teams").insert(record).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                print(f"[DB] Error in create_team: {e}")
                if "PGRST205" in str(e):
                    return self.store.create_team(name, description)
                raise e
        return self.store.create_team(name, description)

    async def delete_team(self, team_id: str) -> bool:
        if self.supabase:
            try:
                self.supabase.table("teams").delete().eq("id", team_id).execute()
                return True
            except Exception as e:
                print(f"[DB] Error in delete_team: {e}")
                if "PGRST205" in str(e):
                    return self.store.delete_team(team_id)
                raise e
        return self.store.delete_team(team_id)

    async def list_team_members(self, team_id: str) -> List[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("team_members").select("user_id").eq("team_id", team_id).execute()
                user_ids = [m["user_id"] for m in (res.data or []) if "user_id" in m]
                if not user_ids:
                    return []
                pres = self.supabase.table("profiles").select("id, name, email, role, avatar_url, created_at").in_("id", user_ids).execute()
                return pres.data or []
            except Exception as e:
                print(f"[DB] Error in list_team_members: {e}")
                if "PGRST205" in str(e):
                    user_ids = [m.get("user_id") for m in self.store.team_members if str(m.get("team_id")) == str(team_id)]
                    members = []
                    for uid in user_ids:
                        p = await self.get_profile(uid)
                        if p:
                            members.append(p)
                    return members
                raise e
        user_ids = [m.get("user_id") for m in self.store.team_members if str(m.get("team_id")) == str(team_id)]
        members = []
        for uid in user_ids:
            p = await self.get_profile(uid)
            if p:
                members.append(p)
        return members

    async def add_team_member(self, team_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        if self.supabase:
            try:
                record = {
                    "team_id": team_id,
                    "user_id": user_id
                }
                res = self.supabase.table("team_members").insert(record).execute()
                if res.data:
                    return res.data[0]
                return None
            except Exception as e:
                err_str = str(e)
                print(f"[DB] Error in add_team_member: {err_str}")
                if "23505" in err_str or "duplicate" in err_str.lower() or "unique" in err_str.lower():
                    return None  # duplicate membership
                if "PGRST205" in err_str:
                    return self.store.add_team_member(team_id, user_id)
                raise e
        return self.store.add_team_member(team_id, user_id)

    async def remove_team_member(self, team_id: str, user_id: str) -> bool:
        if self.supabase:
            try:
                self.supabase.table("team_members").delete().eq("team_id", team_id).eq("user_id", user_id).execute()
                return True
            except Exception as e:
                print(f"[DB] Error in remove_team_member: {e}")
                if "PGRST205" in str(e):
                    return self.store.remove_team_member(team_id, user_id)
                raise e
        return self.store.remove_team_member(team_id, user_id)

    async def get_user_teams(self, user_id: str) -> List[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("team_members").select("team_id").eq("user_id", user_id).execute()
                team_ids = [m["team_id"] for m in (res.data or []) if "team_id" in m]
                if not team_ids:
                    return []
                tres = self.supabase.table("teams").select("*").in_("id", team_ids).execute()
                return tres.data or []
            except Exception as e:
                print(f"[DB] Error in get_user_teams: {e}")
                if "PGRST205" in str(e):
                    return self.store.get_user_teams(user_id)
                raise e
        return self.store.get_user_teams(user_id)

    async def list_teams_with_members(self) -> List[Dict[str, Any]]:
        teams = await self.list_teams()
        if not teams:
            return []
        
        team_map = {str(t["id"]): {**t, "members": []} for t in teams}
        
        if self.supabase:
            try:
                res = self.supabase.table("team_members").select("team_id, user_id").execute()
                memberships = res.data or []
                user_ids = list({m["user_id"] for m in memberships if "user_id" in m})
                profiles_map = {}
                if user_ids:
                    pres = self.supabase.table("profiles").select("id, name, email, role, avatar_url, created_at").in_("id", user_ids).execute()
                    profiles_map = {str(p["id"]): p for p in (pres.data or [])}
                
                for m in memberships:
                    tid = str(m.get("team_id"))
                    uid = str(m.get("user_id"))
                    if tid in team_map and uid in profiles_map:
                        team_map[tid]["members"].append(profiles_map[uid])
                return list(team_map.values())
            except Exception as e:
                print(f"[DB] Error in list_teams_with_members: {e}")
                if "PGRST205" not in str(e):
                    raise e

        # Store fallback / memory store
        for tid, t_obj in team_map.items():
            t_obj["members"] = await self.list_team_members(tid)
        return list(team_map.values())

db = DatabaseRepository()
