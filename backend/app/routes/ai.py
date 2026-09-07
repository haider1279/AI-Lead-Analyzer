from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import uuid
from datetime import datetime, timezone
from ..db.database import db
from ..auth.jwt import get_current_user
from ..models.schemas import (
    AIAnalyzeRequest,
    AIAnalyzeResponse,
    AIConversationAnalysisRequest,
    AIConversationAnalysisResponse
)
from ..ai.gemini_client import ai_service

router = APIRouter(prefix="/leads", tags=["AI Intelligence"])

@router.post("/{lead_id}/analyze", response_model=AIAnalyzeResponse)
async def analyze_lead_endpoint(
    lead_id: str,
    req: AIAnalyzeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    lead = await db.get_lead(lead_id, current_user)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or access denied."
        )

    try:
        analysis_result = ai_service.analyze_lead(lead, req.text)
        
        # Persist structured intelligence to lead
        await db.update_lead(
            lead_id,
            {
                "ai_analysis": analysis_result,
            },
            current_user
        )

        # Cache entry in ai_analyses
        await db.create_ai_analysis({
            "lead_id": lead_id,
            "analysis_type": "FULL_ANALYSIS",
            "input_snapshot": req.text or "Lead context",
            "structured_output": analysis_result,
            "created_by": str(current_user.get("id")) if current_user.get("id") else None,
        })

        return analysis_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to analyze this lead right now. {str(e)}"
        )

@router.post("/{lead_id}/summary")
async def generate_lead_summary_endpoint(
    lead_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    lead = await db.get_lead(lead_id, current_user)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or access denied."
        )

    activities = await db.list_activities_for_lead(lead_id)

    try:
        summary_text = ai_service.generate_summary(lead, activities)
        await db.update_lead(lead_id, {"ai_summary": summary_text}, current_user)
        return {"summary": summary_text}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate AI summary at this moment. Please try again."
        )

@router.post("/{lead_id}/conversation-analysis", response_model=AIConversationAnalysisResponse)
async def analyze_conversation_endpoint(
    lead_id: str,
    req: AIConversationAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    lead = await db.get_lead(lead_id, current_user)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or access denied."
        )

    if len(req.conversation_text) > 15000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conversation text exceeds maximum character limit of 15,000 characters."
        )

    try:
        analysis_result = ai_service.analyze_conversation(req.conversation_text)

        # Cache in ai_analyses
        await db.create_ai_analysis({
            "lead_id": lead_id,
            "analysis_type": "CONVERSATION",
            "input_snapshot": req.conversation_text[:500] + ("..." if len(req.conversation_text) > 500 else ""),
            "structured_output": analysis_result,
            "created_by": str(current_user.get("id")) if current_user.get("id") else None,
        })

        return analysis_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to analyze conversation text right now. Please try again."
        )

@router.post("/{lead_id}/create-action-item")
async def create_action_item_endpoint(
    lead_id: str,
    req: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    lead = await db.get_lead(lead_id, current_user)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or access denied."
        )

    task_data = {
        "lead_id": lead_id,
        "title": req.get("title", "AI Recommended Action"),
        "description": req.get("description", "Action item created from AI Analysis"),
        "priority": req.get("priority", "MEDIUM"),
        "status": "PENDING",
        "due_date": req.get("due_date") or None
    }
    created_task = await db.create_task(task_data, current_user)
    return created_task
