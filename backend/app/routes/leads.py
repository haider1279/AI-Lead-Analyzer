from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from typing import List, Optional, Dict, Any
import json
from ..db.database import db
from ..auth.jwt import get_current_user
from ..auth.permissions import require_admin
from ..models.schemas import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    StatusHistoryResponse,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    ImportPreviewResponse,
    ImportExecuteResponse,
    RejectionDetail,
    LeadDiscoveryResponse,
    BatchVerifyRequest,
    BatchVerifyResponse,
    LeadImportRecord
)
from ..services.duplicate_checker import check_duplicates
from ..services.lead_verifier import LeadVerificationEngine, VERIFICATION_ACCEPTANCE_THRESHOLD
from ..services.lead_importer import LeadDatasetImporter

router = APIRouter(prefix="/leads", tags=["Leads"])

@router.get("", response_model=List[LeadResponse])
async def get_leads(
    search: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
    follow_up_state: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    leads = await db.list_leads(
        current_user=current_user,
        search=search,
        status=status,
        source=source,
        priority=priority,
        assigned_to=assigned_to,
        follow_up_state=follow_up_state
    )
    return leads

@router.post("/check-duplicates", response_model=DuplicateCheckResponse)
@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
async def check_lead_duplicates(
    req: DuplicateCheckRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    all_leads = await db.get_raw_leads()
    matches = check_duplicates(
        company_name=req.company_name,
        email=req.email,
        all_leads=all_leads,
        exclude_id=req.exclude_id
    )
    return DuplicateCheckResponse(
        has_duplicate=len(matches) > 0,
        matches=matches
    )

# --- Dataset Import Routes ---
@router.post("/import/preview", response_model=ImportPreviewResponse)
async def preview_import(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Upload a CSV or XLSX file and get a preview with suggested column mappings."""
    filename = file.filename or "upload.csv"
    fn_lower = filename.lower()
    if not (fn_lower.endswith(".csv") or fn_lower.endswith(".xlsx") or fn_lower.endswith(".xls")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only CSV and XLSX files are supported."
        )
    
    MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the 10 MB limit."
        )
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file is empty."
        )
    
    try:
        preview = LeadDatasetImporter.generate_preview(file_bytes, filename)
        preview["filename"] = filename
        preview["total_rows"] = preview.get("total_preview_rows", 0)
        preview["columns"] = preview.get("detected_headers", [])
        preview["suggested_mapping"] = preview.get("suggested_mappings", {})
        preview["sample_rows"] = preview.get("preview_rows", [])
        return ImportPreviewResponse(**preview)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        print(f"[Import Preview] Error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to parse the uploaded file.")

@router.post("/import", response_model=ImportExecuteResponse, status_code=status.HTTP_200_OK)
async def execute_import(
    file: UploadFile = File(...),
    column_mapping: str = Form(...),
    auto_verify: bool = Form(True),
    source_name: Optional[str] = Form("CSV Import"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Execute a full dataset import with normalization, deduplication, and optional verification."""
    filename = file.filename or "upload.csv"
    fn_lower = filename.lower()
    if not (fn_lower.endswith(".csv") or fn_lower.endswith(".xlsx") or fn_lower.endswith(".xls")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only CSV and XLSX files are supported."
        )

    MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File size exceeds 10 MB limit.")
    if len(file_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="The uploaded file is empty.")

    try:
        mapping = json.loads(column_mapping)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid column_mapping JSON.")

    existing_leads = await db.get_raw_leads()

    try:
        result = await LeadDatasetImporter.process_import_async(
            file_bytes=file_bytes,
            filename=filename,
            column_mapping=mapping,
            existing_leads=existing_leads,
            auto_verify=auto_verify,
            source_name=source_name or "CSV Import",
            created_by_user_id=str(current_user.get("id"))
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        print(f"[Import Execute] Error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Import processing failed.")

    # -----------------------------------------------------------------------
    # 70% GATE ENFORCEMENT & PERSISTENCE
    # Only accepted_leads (score >= 70%) are inserted into Supabase.
    # If insertion fails, raise HTTP 500 — NEVER report fake acceptance!
    # -----------------------------------------------------------------------
    _INTERNAL_KEYS = {"_row_number", "_accepted"}

    leads_to_insert = [
        {k: v for k, v in lead_data.items() if k not in _INTERNAL_KEYS}
        for lead_data in result["accepted_leads"]
    ]

    print(f"[IMPORT] Verification complete: {len(result['accepted_leads'])} accepted, {len(result['rejected_leads'])} rejected")

    if leads_to_insert:
        print(f"[IMPORT] Persisting {len(leads_to_insert)} accepted leads to database...")
        try:
            imported_lead_responses = await db.create_leads_bulk(leads_to_insert, current_user, batch_size=200)
            print(f"[IMPORT] Database persistence successful: {len(imported_lead_responses)} rows stored.")
        except Exception as e:
            print(f"[IMPORT] DATABASE PERSISTENCE FAILED: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database persistence failed: {e}. If verification columns are missing in Supabase, run migration 03_verification_system_upgrade.sql."
            )
    else:
        imported_lead_responses = []

    # Record the overall import in lead_imports table
    import_record_data = {
        "file_name": filename,
        "total_rows": result["total_rows"],
        "valid_rows": result["valid_rows"],
        "invalid_rows": result["invalid_rows"],
        "duplicate_rows": result["duplicate_rows"],
        "verified_rows": result["verified_rows"],
        "unverified_rows": result["unverified_rows"],
        "accepted_rows": len(imported_lead_responses),
        "rejected_rows": result["rejected_rows"],
        "rejection_threshold": result["rejection_threshold"],
        "created_by": str(current_user.get("id"))
    }
    import_rec = await db.create_lead_import_record(import_record_data)

    # Build rejection_details response objects
    rejection_details = [
        RejectionDetail(
            row_number=rd["row_number"],
            company_name=rd["company_name"],
            score=rd["score"],
            reasons=rd["reasons"],
        )
        for rd in result.get("rejection_details", [])
    ]

    return ImportExecuteResponse(
        total_rows=result["total_rows"],
        valid_rows=result["valid_rows"],
        invalid_rows=result["invalid_rows"],
        duplicate_rows=result["duplicate_rows"],
        verified_rows=result["verified_rows"],
        unverified_rows=result["unverified_rows"],
        accepted_rows=len(imported_lead_responses),
        rejected_rows=result["rejected_rows"],
        rejection_threshold=result["rejection_threshold"],
        rejection_details=rejection_details,
        imported_leads=imported_lead_responses,
        import_id=import_rec.get("id")
    )

# --- Discovery & Search Routes ---
@router.get("/discovery/search", response_model=LeadDiscoveryResponse)
async def discovery_search(
    query: Optional[str] = None,
    country: Optional[str] = None,
    industry: Optional[str] = None,
    job_title: Optional[str] = None,
    verification_status: Optional[str] = None,
    min_verification_score: Optional[int] = Query(None, ge=0, le=100),
    is_candidate: Optional[bool] = None,
    source: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search all leads with advanced filters. Includes both candidate and CRM leads."""
    result = await db.discover_leads(
        current_user=current_user,
        query=query,
        country=country,
        industry=industry,
        job_title=job_title,
        verification_status=verification_status,
        min_verification_score=min_verification_score,
        is_candidate=is_candidate,
        source=source,
        page=page,
        page_size=page_size
    )
    return LeadDiscoveryResponse(**result)

@router.get("/verified", response_model=LeadDiscoveryResponse)
async def get_verified_leads(
    query: Optional[str] = None,
    country: Optional[str] = None,
    industry: Optional[str] = None,
    min_verification_score: int = Query(VERIFICATION_ACCEPTANCE_THRESHOLD, ge=VERIFICATION_ACCEPTANCE_THRESHOLD, le=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all verified leads meeting or exceeding the 70% threshold."""
    effective_min_score = max(VERIFICATION_ACCEPTANCE_THRESHOLD, min_verification_score)
    verified_result = await db.discover_leads(
        current_user=current_user,
        query=query,
        country=country,
        industry=industry,
        verification_status="VERIFIED",
        min_verification_score=effective_min_score,
        page=page,
        page_size=page_size
    )
    return LeadDiscoveryResponse(**verified_result)

# --- Imports History ---
@router.get("/imports/history", response_model=List[LeadImportRecord])
async def get_import_history(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get the history of all dataset imports."""
    imports = await db.list_lead_imports(current_user)
    return imports

# --- Single-lead and batch verification ---
@router.post("/{lead_id}/verify", response_model=LeadResponse)
async def verify_lead(
    lead_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Run the verification engine on a single lead."""
    lead = await db.get_lead(lead_id, current_user)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")
    
    verification_result = await LeadVerificationEngine.verify_lead_async(lead)
    updated = await db.update_lead_verification(lead_id, verification_result)
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save verification results.")
    return updated

@router.get("/{lead_id}/verification")
async def get_lead_verification_details(
    lead_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get the full verification details for a specific lead."""
    lead = await db.get_lead(lead_id, current_user)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")
    return {
        "lead_id": lead_id,
        "company_name": lead.get("company_name"),
        "verification_status": lead.get("verification_status", "UNVERIFIED"),
        "verification_score": lead.get("verification_score", 0),
        "verification_details": lead.get("verification_details"),
        "last_verified_at": lead.get("last_verified_at")
    }

@router.post("/verify-batch", response_model=BatchVerifyResponse)
async def batch_verify_leads(
    req: BatchVerifyRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Verify multiple leads (max 25 per request)."""
    if len(req.lead_ids) > 25:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 25 leads can be verified in one batch request."
        )
    results = []
    verified_count = 0
    partially_verified_count = 0
    unverified_count = 0
    rejected_count = 0

    # Fetch all requested leads
    leads_to_verify = []
    lead_id_map = {}
    for lead_id in req.lead_ids:
        try:
            lead = await db.get_lead(lead_id, current_user)
            if lead:
                leads_to_verify.append(lead)
                lead_id_map[len(leads_to_verify) - 1] = lead_id
        except Exception as e:
            print(f"[BatchVerify] Fetch error for lead {lead_id}: {e}")

    if leads_to_verify:
        v_results = await LeadVerificationEngine.verify_leads_batch_async(leads_to_verify, concurrency=20)
        for idx, v_result in enumerate(v_results):
            lead_id = lead_id_map[idx]
            try:
                updated = await db.update_lead_verification(lead_id, v_result)
                if updated:
                    results.append(updated)
                    vs = v_result.get("verification_status", "UNVERIFIED")
                    sc = v_result.get("verification_score", 0)
                    if vs == "VERIFIED" or sc >= VERIFICATION_ACCEPTANCE_THRESHOLD:
                        verified_count += 1
                    elif vs == "REJECTED" or sc < VERIFICATION_ACCEPTANCE_THRESHOLD:
                        rejected_count += 1
                    else:
                        unverified_count += 1
            except Exception as e:
                print(f"[BatchVerify] Update error for lead {lead_id}: {e}")
                unverified_count += 1

    return BatchVerifyResponse(
        total_requested=len(req.lead_ids),
        verified_count=verified_count,
        partially_verified_count=0,
        unverified_count=unverified_count,
        rejected_count=rejected_count,
        results=results
    )

@router.post("/{lead_id}/promote", response_model=LeadResponse)
async def promote_candidate_to_crm(
    lead_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Promote a candidate lead to a full CRM opportunity. Only allowed if verification score >= 70%."""
    lead = await db.get_lead(lead_id, current_user)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")
    
    score = lead.get("verification_score") or 0
    if score < VERIFICATION_ACCEPTANCE_THRESHOLD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot promote lead into CRM. Verification score ({score}%) is below the required {VERIFICATION_ACCEPTANCE_THRESHOLD}% acceptance threshold."
        )

    promoted = await db.promote_candidate_to_crm(lead_id, current_user)
    if not promoted:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to promote lead.")
    return promoted

# --- Standard lead CRUD ---
@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_in: LeadCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    if not lead_in.company_name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Company name cannot be empty."
        )
    lead_data = lead_in.model_dump(mode='json')
    created_lead = await db.create_lead(lead_data, current_user)
    return created_lead

@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead_by_id(
    lead_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    lead = await db.get_lead(lead_id, current_user)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or you do not have permission to view it."
        )
    return lead

@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_in: LeadUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    updates = lead_in.model_dump(exclude_unset=True, mode='json')
    updated = await db.update_lead(lead_id, updates, current_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or you do not have permission to update it."
        )
    return updated

@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    success = await db.delete_lead(lead_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or deletion failed."
        )
    return None

@router.get("/{lead_id}/history", response_model=List[StatusHistoryResponse])
async def get_lead_status_history(
    lead_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    lead = await db.get_lead(lead_id, current_user)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or access denied."
        )
    history = await db.list_status_history(lead_id)
    return history
