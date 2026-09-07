from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from ..db.database import db
from ..auth.jwt import get_current_user
from ..auth.permissions import require_admin
from ..models.schemas import TeamCreate, TeamUpdate, TeamMemberAdd, TeamResponse, TeamWithMembersResponse

router = APIRouter(prefix="/teams", tags=["Teams"])


# ─── List all teams (with members) ──────────────────────────────────────────

@router.get("", response_model=List[TeamWithMembersResponse])
async def list_teams(current_user: Dict[str, Any] = Depends(get_current_user)):
    """List all teams with their member profiles. Accessible by any authenticated user."""
    teams = await db.list_teams_with_members()
    return teams


# ─── Create a new team (admin only) ─────────────────────────────────────────

@router.post("", response_model=TeamWithMembersResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    body: TeamCreate,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Create a new team. Admin only."""
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Team name cannot be empty.")

    existing = await db.get_team_by_name(name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A team named '{name}' already exists."
        )

    team = await db.create_team(name, body.description)
    team["members"] = []
    return team


# ─── Get a single team with members ─────────────────────────────────────────

@router.get("/{team_id}", response_model=TeamWithMembersResponse)
async def get_team(
    team_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a single team with its member list."""
    team = await db.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")
    members = await db.list_team_members(team_id)
    team["members"] = members
    return team


# ─── Update a team (admin only) ──────────────────────────────────────────────

@router.put("/{team_id}", response_model=TeamWithMembersResponse)
async def update_team(
    team_id: str,
    body: TeamUpdate,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Update a team's name or description. Admin only."""
    team = await db.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")

    updates = {}
    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Team name cannot be empty.")
        updates["name"] = name
    if body.description is not None:
        updates["description"] = body.description.strip() or None

    if updates:
        if db.supabase:
            try:
                res = db.supabase.table("teams").update(updates).eq("id", team_id).execute()
                if res.data:
                    team = res.data[0]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to update team: {e}")
        else:
            for k, v in updates.items():
                team[k] = v

    members = await db.list_team_members(team_id)
    team["members"] = members
    return team


# ─── Delete a team (admin only) ──────────────────────────────────────────────

@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: str,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Delete a team and all its memberships. Admin only."""
    team = await db.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")

    # Remove all member associations first
    if db.supabase:
        try:
            db.supabase.table("team_members").delete().eq("team_id", team_id).execute()
        except Exception:
            pass  # Non-fatal if table doesn't exist yet

    success = await db.delete_team(team_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete team.")
    return None


# ─── List members of a team ──────────────────────────────────────────────────

@router.get("/{team_id}/members", response_model=List[Dict[str, Any]])
async def list_team_members(
    team_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all members of a team."""
    team = await db.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")
    members = await db.list_team_members(team_id)
    return members


# ─── Add a member to a team (admin only) ─────────────────────────────────────

@router.post("/{team_id}/members", status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: str,
    body: TeamMemberAdd,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Add an existing user to a team. Admin only. Does not change the user's role."""
    team = await db.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")

    # Verify the user exists
    profile = await db.get_profile(body.user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found.")

    result = await db.add_team_member(team_id, body.user_id)
    # None can be returned for duplicate membership — treat as success
    return {"message": "Member added successfully.", "team_id": team_id, "user_id": body.user_id}


# ─── Remove a member from a team (admin only) ────────────────────────────────

@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: str,
    user_id: str,
    admin: Dict[str, Any] = Depends(require_admin)
):
    """Remove a user from a team. Admin only. Does not change the user's role."""
    team = await db.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")

    await db.remove_team_member(team_id, user_id)
    return None


# ─── List teams a specific user belongs to ───────────────────────────────────

@router.get("/user/{user_id}", response_model=List[TeamResponse])
async def get_user_teams(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all teams a user belongs to."""
    teams = await db.get_user_teams(user_id)
    return teams
