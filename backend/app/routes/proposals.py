from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List, Dict, Any, Optional
from ..db.database import db
from ..auth.jwt import get_current_user
from ..models.schemas import (
    ProposalGenerateRequest,
    ProposalSaveRequest,
    ProposalResponse
)
from ..ai.gemini_client import ai_service
from ..services.pdf_generator import generate_proposal_pdf

router = APIRouter(tags=["Proposals"])

@router.post("/leads/{lead_id}/proposal")
@router.post("/proposals/draft/{lead_id}")
async def generate_proposal_draft(
    lead_id: str,
    req: ProposalGenerateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    lead = await db.get_lead(lead_id, current_user)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or access denied."
        )

    try:
        draft = ai_service.generate_proposal(lead, req.custom_notes)
        return {
            "title": f"Proposal: {lead.get('project_title') or lead.get('company_name')} Solution",
            "content": draft
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate proposal draft at this time. Please try again."
        )

@router.get("/leads/{lead_id}/proposals", response_model=List[ProposalResponse])
@router.get("/proposals/lead/{lead_id}", response_model=List[ProposalResponse])
async def list_proposals(
    lead_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    lead = await db.get_lead(lead_id, current_user)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or access denied."
        )
    proposals = await db.list_proposals_for_lead(lead_id)
    return proposals

@router.post("/leads/{lead_id}/proposals/save", response_model=ProposalResponse)
@router.post("/proposals", response_model=ProposalResponse)
async def save_proposal_endpoint(
    req: ProposalSaveRequest,
    lead_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    target_lead_id = lead_id or req.lead_id
    if not target_lead_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="lead_id is required."
        )

    lead = await db.get_lead(target_lead_id, current_user)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or access denied."
        )

    saved = await db.save_proposal(
        lead_id=target_lead_id,
        title=req.title,
        content=req.content,
        status=req.status.value,
        current_user=current_user
    )
    
    if req.status.value == "SENT":
        await db.create_activity(
            lead_id=target_lead_id,
            act_data={
                "type": "Proposal Sent",
                "title": f"Sent proposal: {req.title}",
                "description": f"Commercial proposal delivered to {lead.get('contact_name') or lead.get('company_name')}.",
                "outcome": "Awaiting client feedback",
                "next_action": "Follow up in 3 business days"
            },
            current_user=current_user
        )

    return saved

@router.get("/proposals/{proposal_id}", response_model=ProposalResponse)
async def get_proposal_by_id(
    proposal_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    proposal = await db.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    return proposal

@router.put("/proposals/{proposal_id}", response_model=ProposalResponse)
async def update_proposal_by_id(
    proposal_id: str,
    updates: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    updated = await db.update_proposal(proposal_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    return updated

@router.get("/proposals/{proposal_id}/pdf")
async def download_proposal_pdf(
    proposal_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    proposal = await db.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")

    lead = await db.get_lead(proposal["lead_id"], current_user)
    if not lead:
        raise HTTPException(status_code=404, detail="Associated lead not found or access denied.")

    try:
        pdf_bytes = generate_proposal_pdf(lead, proposal)
        filename = f"Euroshub_Proposal_{lead.get('company_name', 'Client').replace(' ', '_')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate proposal PDF: {str(e)}"
        )
