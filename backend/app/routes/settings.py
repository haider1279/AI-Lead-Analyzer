from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from ..db.database import db
from ..auth.jwt import get_current_user
from ..auth.permissions import require_admin
from ..models.schemas import LeadSourceCreate, LeadSourceResponse
from ..utils.config import settings

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/sources", response_model=List[LeadSourceResponse])
async def get_lead_sources(current_user: Dict[str, Any] = Depends(get_current_user)):
    sources = await db.list_lead_sources()
    return sources

@router.post("/sources", response_model=LeadSourceResponse, status_code=status.HTTP_201_CREATED)
async def add_lead_source(
    req: LeadSourceCreate,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Lead source name cannot be empty.")
    source = await db.create_lead_source(req.name)
    return source

@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_lead_source(
    source_id: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    success = await db.delete_lead_source(source_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead source not found.")
    return None

@router.get("/system")
async def get_system_config(current_user: Dict[str, Any] = Depends(get_current_user)):
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "ai_model": settings.GEMINI_MODEL,
        "supabase_connected": db.supabase is not None,
        "database_mode": "Supabase PostgreSQL" if db.supabase else "Memory / Local Persistent Store"
    }
