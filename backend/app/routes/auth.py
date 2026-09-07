from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from ..db.database import db
from ..auth.jwt import get_current_user
from ..auth.permissions import require_admin
from ..models.schemas import UserProfile, UserUpdate, AdminUserCreate

router = APIRouter(prefix="/auth", tags=["Auth & Profiles"])

@router.get("/me", response_model=UserProfile)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserProfile)
async def update_me(update_data: UserUpdate, current_user: Dict[str, Any] = Depends(get_current_user)):
    updates = {}
    if update_data.name is not None:
        updates["name"] = update_data.name
    if update_data.avatar_url is not None:
        updates["avatar_url"] = update_data.avatar_url
    
    # Only admin can change role
    if update_data.role is not None:
        if current_user.get("role") == "admin":
            updates["role"] = update_data.role.value
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can change user roles."
            )

    updated = await db.update_profile(current_user["id"], updates)
    if not updated:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return updated

@router.get("/users", response_model=List[UserProfile])
async def list_users(current_user: Dict[str, Any] = Depends(get_current_user)):
    # Authenticated employees can list user names for assignment dropdowns
    profiles = await db.list_profiles()
    return profiles

@router.post("/users", response_model=UserProfile)
async def create_user_admin(user_in: AdminUserCreate, admin: Dict[str, Any] = Depends(require_admin)):
    existing = await db.get_profile_by_email(user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user_in.email} already exists."
        )

    import uuid
    from datetime import datetime, timezone
    new_user = {
        "id": str(uuid.uuid4()),
        "email": user_in.email.lower().strip(),
        "name": user_in.name.strip(),
        "role": user_in.role.value,
        "avatar_url": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    created = await db.create_profile(new_user)
    return created

@router.put("/users/{user_id}/role", response_model=UserProfile)
async def change_user_role(user_id: str, update_data: UserUpdate, admin: Dict[str, Any] = Depends(require_admin)):
    if not update_data.role:
        raise HTTPException(status_code=400, detail="Role must be provided.")
    
    updated = await db.update_profile(user_id, {"role": update_data.role.value})
    if not updated:
        raise HTTPException(status_code=404, detail="User not found.")
    return updated
