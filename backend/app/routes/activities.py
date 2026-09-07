from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from ..db.database import db
from ..auth.jwt import get_current_user
from ..models.schemas import ActivityCreate, ActivityResponse

router = APIRouter(prefix="/leads", tags=["Activities"])

@router.get("/{lead_id}/activities", response_model=List[ActivityResponse])
@router.get("/activities/lead/{lead_id}", response_model=List[ActivityResponse])
async def get_lead_activities(
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
    return activities

@router.post("/{lead_id}/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_lead_activity(
    lead_id: str,
    activity_in: ActivityCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    lead = await db.get_lead(lead_id, current_user)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or access denied."
        )
    
    act_data = activity_in.model_dump()
    created = await db.create_activity(lead_id, act_data, current_user)
    return created

@router.post("/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity_direct(
    activity_in: ActivityCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    lead_id = activity_in.lead_id
    if not lead_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="lead_id is required."
        )
    lead = await db.get_lead(lead_id, current_user)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or access denied."
        )
    act_data = activity_in.model_dump()
    created = await db.create_activity(lead_id, act_data, current_user)
    return created
