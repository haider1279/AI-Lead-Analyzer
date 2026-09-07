from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from ..db.database import db
from ..auth.jwt import get_current_user
from ..models.schemas import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("", response_model=List[TaskResponse])
async def get_tasks(
    lead_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    tasks = await db.list_tasks(
        current_user=current_user,
        lead_id=lead_id,
        assigned_to=assigned_to,
        status=status
    )
    return tasks

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    task_data = task_in.model_dump()
    created = await db.create_task(task_data, current_user)
    return created

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_in: TaskUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    updates = task_in.model_dump(exclude_unset=True)
    updated = await db.update_task(task_id, updates, current_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or access denied."
        )
    return updated

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    success = await db.delete_task(task_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or permission denied."
        )
    return None
