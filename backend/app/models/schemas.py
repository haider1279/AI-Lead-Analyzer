from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Dict
from datetime import date, datetime
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    employee = "employee"


# --- User / Profile Schemas ---

class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    role: str
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[UserRole] = None


class AdminUserCreate(BaseModel):
    email: str
    name: str
    role: UserRole = UserRole.employee


# --- Lead Schemas ---

class LeadCreate(BaseModel):
    company_name: str
    contact_name: Optional[str] = None
    job_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    source: Optional[str] = "Upwork"
    custom_source: Optional[str] = None
    project_title: Optional[str] = None
    project_description: Optional[str] = None
    budget: Optional[float] = 0.0
    currency: Optional[str] = "USD"
    expected_deadline: Optional[date] = None
    priority: Optional[str] = "MEDIUM"
    status: Optional[str] = "NEW"
    assigned_to: Optional[str] = None
    follow_up_date: Optional[str] = None
    is_candidate: Optional[bool] = False
    source_record_id: Optional[str] = None
    normalized_email: Optional[str] = None
    normalized_phone: Optional[str] = None
    normalized_company: Optional[str] = None


class LeadUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    job_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    source: Optional[str] = None
    custom_source: Optional[str] = None
    project_title: Optional[str] = None
    project_description: Optional[str] = None
    budget: Optional[float] = None
    currency: Optional[str] = None
    expected_deadline: Optional[date] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    follow_up_date: Optional[str] = None
    notes: Optional[str] = None
    is_candidate: Optional[bool] = None


class LeadResponse(BaseModel):
    id: str
    company_name: str
    contact_name: Optional[str] = None
    job_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    source: Optional[str] = None
    custom_source: Optional[str] = None
    project_title: Optional[str] = None
    project_description: Optional[str] = None
    budget: Optional[float] = None
    currency: Optional[str] = None
    expected_deadline: Optional[Any] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_user: Optional[Dict[str, Any]] = None
    creator_user: Optional[Dict[str, Any]] = None
    follow_up_date: Optional[str] = None
    lead_score: Optional[int] = None
    lead_score_label: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_analysis: Optional[Any] = None
    verification_status: Optional[str] = "UNVERIFIED"
    verification_score: Optional[int] = 0
    verification_details: Optional[Any] = None
    last_verified_at: Optional[str] = None
    is_candidate: Optional[bool] = False
    source_record_id: Optional[str] = None
    normalized_email: Optional[str] = None
    normalized_phone: Optional[str] = None
    normalized_company: Optional[str] = None
    activities_count: Optional[int] = 0
    tasks_count: Optional[int] = 0
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class StatusHistoryResponse(BaseModel):
    id: Optional[str] = None
    lead_id: str
    old_status: Optional[str] = None
    new_status: str
    changed_by: Optional[str] = None
    changed_at: Optional[str] = None

    class Config:
        from_attributes = True


# --- Duplicate Check Schemas ---

class DuplicateMatch(BaseModel):
    lead_id: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    contact_name: Optional[str] = None
    status: Optional[str] = None
    match_reason: str

    class Config:
        from_attributes = True


class DuplicateCheckRequest(BaseModel):
    company_name: Optional[str] = None
    email: Optional[str] = None
    exclude_id: Optional[str] = None


class DuplicateCheckResponse(BaseModel):
    has_duplicate: bool
    matches: List[DuplicateMatch] = []


# --- Import / Preview Schemas ---

class ColumnPreview(BaseModel):
    csv_column: str
    suggested_field: Optional[str] = None
    sample_values: List[Any] = []


class ImportPreviewResponse(BaseModel):
    # Discovery & Radar import preview fields (matching frontend DatasetImportModal)
    total_preview_rows: Optional[int] = None
    detected_headers: Optional[List[str]] = []
    suggested_mappings: Optional[Dict[str, str]] = {}
    preview_rows: Optional[List[Dict[str, Any]]] = []

    # Backward-compatible fields
    filename: Optional[str] = None
    total_rows: Optional[int] = None
    columns: Optional[List[str]] = []
    column_previews: Optional[List[ColumnPreview]] = []
    sample_rows: Optional[List[Dict[str, Any]]] = []
    suggested_mapping: Optional[Dict[str, str]] = {}


class RejectionDetail(BaseModel):
    row_number: int
    company_name: Optional[str] = None
    score: int
    reasons: List[str] = []


class ImportExecuteResponse(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    verified_rows: int
    unverified_rows: int
    accepted_rows: int
    rejected_rows: int
    rejection_threshold: int
    rejection_details: List[RejectionDetail] = []
    imported_leads: List[Dict[str, Any]] = []
    import_id: Optional[str] = None


class LeadImportRecord(BaseModel):
    id: Optional[str] = None
    file_name: Optional[str] = None
    total_rows: Optional[int] = 0
    valid_rows: Optional[int] = 0
    invalid_rows: Optional[int] = 0
    duplicate_rows: Optional[int] = 0
    verified_rows: Optional[int] = 0
    unverified_rows: Optional[int] = 0
    accepted_rows: Optional[int] = 0
    rejected_rows: Optional[int] = 0
    rejection_threshold: Optional[int] = 70
    created_by: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


# --- Discovery / Verification Schemas ---

class LeadDiscoveryResponse(BaseModel):
    leads: List[Dict[str, Any]] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 1


class BatchVerifyRequest(BaseModel):
    lead_ids: List[str]


class BatchVerifyResponse(BaseModel):
    total_requested: int
    verified_count: int
    partially_verified_count: int
    unverified_count: int
    rejected_count: int
    results: List[Dict[str, Any]] = []


# --- Activity Schemas ---

class ActivityCreate(BaseModel):
    lead_id: Optional[str] = None
    type: str
    title: str
    description: Optional[str] = None
    outcome: Optional[str] = None
    next_action: Optional[str] = None
    activity_date: Optional[str] = None
    follow_up_date: Optional[str] = None


class ActivityResponse(BaseModel):
    id: Optional[str] = None
    lead_id: Optional[str] = None
    user_id: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    type: str
    title: str
    description: Optional[str] = None
    outcome: Optional[str] = None
    next_action: Optional[str] = None
    activity_date: Optional[str] = None
    follow_up_date: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


# --- Task Schemas ---

class TaskCreate(BaseModel):
    lead_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = "MEDIUM"
    status: Optional[str] = "PENDING"
    assigned_to: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None


class TaskResponse(BaseModel):
    id: Optional[str] = None
    lead_id: Optional[str] = None
    user_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_user: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


# --- Proposal Schemas ---

class ProposalGenerateRequest(BaseModel):
    tone: Optional[str] = "professional"
    custom_notes: Optional[str] = None
    include_timeline: Optional[bool] = True
    include_pricing: Optional[bool] = True


class ProposalSaveRequest(BaseModel):
    title: Optional[str] = None
    content: str
    tone: Optional[str] = None
    status: Optional[str] = "draft"


class ProposalResponse(BaseModel):
    id: Optional[str] = None
    lead_id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    tone: Optional[str] = None
    status: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


# --- AI Schemas ---

class AIAnalyzeRequest(BaseModel):
    force_refresh: Optional[bool] = False


class AIAnalyzeResponse(BaseModel):
    lead_id: str
    lead_score: Optional[int] = None
    lead_score_label: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    analyzed_at: Optional[str] = None

    class Config:
        from_attributes = True


class AIConversationAnalysisRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


class AIConversationAnalysisResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None
    context_used: Optional[bool] = False

    class Config:
        from_attributes = True


# --- Lead Source Schemas ---

class LeadSourceCreate(BaseModel):
    name: str


class LeadSourceResponse(BaseModel):
    id: str
    name: str
    is_active: Optional[bool] = True
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


# --- Team Schemas ---

class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TeamMemberAdd(BaseModel):
    user_id: str


class TeamResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class TeamWithMembersResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    members: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True
