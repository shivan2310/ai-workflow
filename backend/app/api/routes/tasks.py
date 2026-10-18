import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, get_db
from app.schemas.auth import AuthenticatedUser
from app.schemas.workflow import TaskDetailResponse, TaskListResponse
from app.db.repositories import TaskRepository

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse)
def list_tasks(
    workflow_id: Optional[uuid.UUID] = Query(None, description="Optional workflow filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns tasks belonging only to the authenticated user, optionally
    filtered by workflow ID.
    """
    task_repo = TaskRepository(db)
    tasks, total = task_repo.list_by_user(
        user_id=current_user.id,
        workflow_id=workflow_id,
        skip=skip,
        limit=limit,
    )

    items = [
        TaskDetailResponse(
            id=t.id,
            workflow_id=t.workflow_id,
            task_key=t.task_key,
            description=t.description,
            tool_name=t.tool_name,
            status=t.status,
            result=t.result_json,
            error_message=t.error_message,
            created_at=t.created_at,
            started_at=t.started_at,
            completed_at=t.completed_at,
        )
        for t in tasks
    ]

    return TaskListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )
