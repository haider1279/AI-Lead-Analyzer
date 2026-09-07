import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

DATA_FILE = os.path.join(os.path.dirname(__file__), 'mock_db_data.json')

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def days_from_now(days: int):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()

DEFAULT_PROFILES = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "admin@euroshub.com",
        "name": "Alex Rivers (Admin)",
        "role": "admin",
        "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
        "created_at": now_iso()
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "email": "sarah.sales@euroshub.com",
        "name": "Sarah Chen (Lead Closer)",
        "role": "employee",
        "avatar_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80",
        "created_at": now_iso()
    },
    {
        "id": "00000000-0000-0000-0000-000000000003",
        "email": "david.tech@euroshub.com",
        "name": "David Miller (Solutions Architect)",
        "role": "employee",
        "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
        "created_at": now_iso()
    }
]

DEFAULT_SOURCES = [
    {"id": str(uuid.uuid4()), "name": "Upwork", "is_active": True, "created_at": now_iso()},
    {"id": str(uuid.uuid4()), "name": "LinkedIn", "is_active": True, "created_at": now_iso()},
    {"id": str(uuid.uuid4()), "name": "WhatsApp", "is_active": True, "created_at": now_iso()},
    {"id": str(uuid.uuid4()), "name": "Email", "is_active": True, "created_at": now_iso()},
    {"id": str(uuid.uuid4()), "name": "Website", "is_active": True, "created_at": now_iso()},
    {"id": str(uuid.uuid4()), "name": "Referral", "is_active": True, "created_at": now_iso()},
    {"id": str(uuid.uuid4()), "name": "Phone", "is_active": True, "created_at": now_iso()},
    {"id": str(uuid.uuid4()), "name": "Other", "is_active": True, "created_at": now_iso()}
]

DEFAULT_LEADS = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "company_name": "FinTech Horizon Ltd",
        "contact_name": "Marcus Sterling",
        "email": "marcus@fintechhorizon.co.uk",
        "phone": "+44 20 7946 0912",
        "website": "https://fintechhorizon.co.uk",
        "industry": "Financial Services",
        "country": "United Kingdom",
        "source": "Upwork",
        "custom_source": None,
        "project_title": "Next-Gen AI Wealth Advisory Portal",
        "project_description": "Client needs a secure SaaS portal with real-time portfolio analytics, automated rebalancing recommendations powered by AI, and interactive charts.",
        "budget": 38000.0,
        "currency": "USD",
        "expected_deadline": "2026-11-30",
        "priority": "HIGH",
        "status": "QUALIFIED",
        "assigned_to": "00000000-0000-0000-0000-000000000002",
        "follow_up_date": days_from_now(1),
        "lead_score": 88,
        "lead_score_label": "HIGH POTENTIAL",
        "ai_summary": "High-value FinTech opportunity with clearly articulated scope and healthy budget. Client is technically savvy and requires delivery in Q4.",
        "ai_analysis": {
            "project_type": "FinTech SaaS Web Application",
            "complexity": "High",
            "potential_risks": ["Real-time financial data security compliance", "Integration with banking APIs"],
            "recommended_next_action": "Send technical architecture draft and schedule 30-min discovery call"
        },
        "created_by": "00000000-0000-0000-0000-000000000001",
        "created_at": days_from_now(-5),
        "updated_at": days_from_now(-1)
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "company_name": "Nordic Logistics Hub",
        "contact_name": "Elena Lindqvist",
        "email": "elena.l@nordichub.se",
        "phone": "+46 8 123 4567",
        "website": "https://nordichub.se",
        "industry": "Supply Chain & Logistics",
        "country": "Sweden",
        "source": "LinkedIn",
        "custom_source": None,
        "project_title": "Automated Fleet Tracking & Dispatch System",
        "project_description": "Centralized telemetry dashboard for 350+ trucks across Scandinavia with route optimization and driver mobile application.",
        "budget": 52000.0,
        "currency": "USD",
        "expected_deadline": "2026-12-15",
        "priority": "URGENT",
        "status": "PROPOSAL_SENT",
        "assigned_to": "00000000-0000-0000-0000-000000000002",
        "follow_up_date": days_from_now(2),
        "lead_score": 92,
        "lead_score_label": "HOT PROSPECT",
        "ai_summary": "Large-scale enterprise telematics project. Technical proposal submitted yesterday. Decision maker is very responsive.",
        "ai_analysis": {
            "project_type": "IoT Logistics Dashboard & Mobile App",
            "complexity": "Very High",
            "potential_risks": ["Scalability of GPS websocket ingestion", "Offline sync for driver app"],
            "recommended_next_action": "Follow up regarding proposal feedback on Thursday"
        },
        "created_by": "00000000-0000-0000-0000-000000000001",
        "created_at": days_from_now(-10),
        "updated_at": days_from_now(-2)
    }
]

DEFAULT_ACTIVITIES = [
    {
        "id": str(uuid.uuid4()),
        "lead_id": "11111111-1111-1111-1111-111111111111",
        "user_id": "00000000-0000-0000-0000-000000000002",
        "type": "CALL",
        "title": "Initial Discovery Call",
        "description": "Discussed core requirements for AI robo-advisor features and tech stack preference (React + FastAPI).",
        "created_at": days_from_now(-4)
    },
    {
        "id": str(uuid.uuid4()),
        "lead_id": "22222222-2222-2222-2222-222222222222",
        "user_id": "00000000-0000-0000-0000-000000000002",
        "type": "EMAIL",
        "title": "Sent Full Technical Proposal",
        "description": "Emailed comprehensive 14-page PDF proposal detailing architecture, sprint breakdown, and fixed quote.",
        "created_at": days_from_now(-2)
    }
]

DEFAULT_TASKS = [
    {
        "id": str(uuid.uuid4()),
        "lead_id": "11111111-1111-1111-1111-111111111111",
        "title": "Prepare High-Level Architecture Diagram",
        "description": "Draft cloud infrastructure setup diagram covering AWS ECS, RDS PostgreSQL, and Redis caching.",
        "assigned_to": "00000000-0000-0000-0000-000000000003",
        "due_date": days_from_now(1),
        "status": "IN_PROGRESS",
        "priority": "HIGH",
        "created_by": "00000000-0000-0000-0000-000000000001",
        "created_at": days_from_now(-3),
        "updated_at": days_from_now(-1)
    },
    {
        "id": str(uuid.uuid4()),
        "lead_id": "22222222-2222-2222-2222-222222222222",
        "title": "Follow up on proposal review",
        "description": "Ping Elena on LinkedIn / Email to schedule a proposal review walkthrough call.",
        "assigned_to": "00000000-0000-0000-0000-000000000002",
        "due_date": days_from_now(2),
        "status": "PENDING",
        "priority": "MEDIUM",
        "created_by": "00000000-0000-0000-0000-000000000001",
        "created_at": days_from_now(-2),
        "updated_at": days_from_now(-2)
    }
]

DEFAULT_PROPOSALS = [
    {
        "id": str(uuid.uuid4()),
        "lead_id": "22222222-2222-2222-2222-222222222222",
        "version": 1,
        "title": "Turnkey Telematics & Dispatch Platform Architecture",
        "content": {
            "summary": "Full-stack real-time telemetry tracking system for commercial vehicle fleets.",
            "deliverables": [
                "Real-time GPS dashboard with sub-second WebSocket updates",
                "Cross-platform Driver Mobile Application (React Native)",
                "Deployment to AWS with CI/CD and automated backups",
                "3 Months Post-Launch Warranty & Support"
            ],
            "timeline": "12 Weeks across 4 Milestones",
            "pricing": "$52,000 USD (Fixed Price across 4 milestone payments)",
            "assumptions": [
                "Hardware devices output data via standard HTTP/MQTT payload",
                "Nordic Logistics team provides API credentials for existing ERP"
            ],
            "next_steps": "Sign formal contract, submit initial milestone deposit (25%), and initiate Sprint 0 discovery workshop."
        },
        "status": "SENT",
        "created_at": days_from_now(-2),
        "updated_at": days_from_now(-1)
    }
]

DEFAULT_STATUS_HISTORY = [
    {
        "id": str(uuid.uuid4()),
        "lead_id": "11111111-1111-1111-1111-111111111111",
        "old_status": None,
        "new_status": "NEW",
        "changed_by": "00000000-0000-0000-0000-000000000001",
        "changed_at": days_from_now(-5)
    },
    {
        "id": str(uuid.uuid4()),
        "lead_id": "11111111-1111-1111-1111-111111111111",
        "old_status": "NEW",
        "new_status": "CONTACTED",
        "changed_by": "00000000-0000-0000-0000-000000000002",
        "changed_at": days_from_now(-3)
    },
    {
        "id": str(uuid.uuid4()),
        "lead_id": "11111111-1111-1111-1111-111111111111",
        "old_status": "CONTACTED",
        "new_status": "QUALIFIED",
        "changed_by": "00000000-0000-0000-0000-000000000002",
        "changed_at": days_from_now(-2)
    }
]

DEFAULT_TEAMS = [
    {
        "id": "t1111111-1111-1111-1111-111111111111",
        "name": "Sales Team",
        "description": "Direct outbound sales and deal closing",
        "created_at": now_iso(),
        "updated_at": now_iso()
    },
    {
        "id": "t2222222-2222-2222-2222-222222222222",
        "name": "Management Team",
        "description": "Executive leadership and operations",
        "created_at": now_iso(),
        "updated_at": now_iso()
    },
    {
        "id": "t3333333-3333-3333-3333-333333333333",
        "name": "Lead Research Team",
        "description": "Prospecting, intelligence gathering, and qualification",
        "created_at": now_iso(),
        "updated_at": now_iso()
    }
]

class MemoryStore:
    def __init__(self):
        self.profiles: List[Dict[str, Any]] = list(DEFAULT_PROFILES)
        self.lead_sources: List[Dict[str, Any]] = list(DEFAULT_SOURCES)
        self.leads: List[Dict[str, Any]] = list(DEFAULT_LEADS)
        self.activities: List[Dict[str, Any]] = list(DEFAULT_ACTIVITIES)
        self.tasks: List[Dict[str, Any]] = list(DEFAULT_TASKS)
        self.proposals: List[Dict[str, Any]] = list(DEFAULT_PROPOSALS)
        self.status_history: List[Dict[str, Any]] = list(DEFAULT_STATUS_HISTORY)
        self.ai_analyses: List[Dict[str, Any]] = []
        self.teams: List[Dict[str, Any]] = [dict(t) for t in DEFAULT_TEAMS]
        self.team_members: List[Dict[str, Any]] = []

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        for p in self.profiles:
            if str(p.get("id")) == str(user_id):
                return p
        return None

    def get_profile_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        for p in self.profiles:
            if p.get("email", "").lower() == email.lower():
                return p
        return None

    def create_or_update_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        existing = self.get_profile(profile_data["id"])
        if existing:
            existing.update(profile_data)
            return existing
        else:
            self.profiles.append(profile_data)
            return profile_data

    # --- Teams Memory Store Methods ---
    def list_teams(self) -> List[Dict[str, Any]]:
        return [dict(t) for t in self.teams]

    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        for t in self.teams:
            if str(t.get("id")) == str(team_id):
                return dict(t)
        return None

    def get_team_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        for t in self.teams:
            if t.get("name", "").strip().lower() == name.strip().lower():
                return dict(t)
        return None

    def create_team(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        now = now_iso()
        new_team = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "description": description.strip() if description else None,
            "created_at": now,
            "updated_at": now
        }
        self.teams.append(new_team)
        return dict(new_team)

    def delete_team(self, team_id: str) -> bool:
        idx = None
        for i, t in enumerate(self.teams):
            if str(t.get("id")) == str(team_id):
                idx = i
                break
        if idx is not None:
            self.teams.pop(idx)
            # Cascade: delete memberships
            self.team_members = [m for m in self.team_members if str(m.get("team_id")) != str(team_id)]
            return True
        return False

    def list_team_members(self, team_id: str) -> List[Dict[str, Any]]:
        user_ids = {str(m.get("user_id")) for m in self.team_members if str(m.get("team_id")) == str(team_id)}
        members = []
        for p in self.profiles:
            if str(p.get("id")) in user_ids:
                members.append(dict(p))
        return members

    def add_team_member(self, team_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        for m in self.team_members:
            if str(m.get("team_id")) == str(team_id) and str(m.get("user_id")) == str(user_id):
                return None
        record = {
            "id": str(uuid.uuid4()),
            "team_id": str(team_id),
            "user_id": str(user_id),
            "created_at": now_iso()
        }
        self.team_members.append(record)
        return record

    def remove_team_member(self, team_id: str, user_id: str) -> bool:
        idx = None
        for i, m in enumerate(self.team_members):
            if str(m.get("team_id")) == str(team_id) and str(m.get("user_id")) == str(user_id):
                idx = i
                break
        if idx is not None:
            self.team_members.pop(idx)
            return True
        return False

    def get_user_teams(self, user_id: str) -> List[Dict[str, Any]]:
        team_ids = {str(m.get("team_id")) for m in self.team_members if str(m.get("user_id")) == str(user_id)}
        return [dict(t) for t in self.teams if str(t.get("id")) in team_ids]

store = MemoryStore()
