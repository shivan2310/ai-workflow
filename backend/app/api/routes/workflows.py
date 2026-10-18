import uuid
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks, Query, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, get_db
from app.schemas.auth import AuthenticatedUser
from app.schemas.workflow import (
    WorkflowCreateRequest,
    WorkflowSummaryResponse,
    WorkflowDetailResponse,
    WorkflowListResponse,
)
from app.db.repositories import WorkflowRepository
from app.services.orchestrator import WorkflowOrchestrator
from app.core.exceptions import ResourceNotFoundError, WorkflowConflictError

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=WorkflowSummaryResponse)
async def create_workflow(
    payload: WorkflowCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submits a natural language goal. Derives user_id from verified token,
    persists the initial workflow, and initiates async background execution.
    """
    wf_repo = WorkflowRepository(db)
    workflow = wf_repo.create(
        user_id=current_user.id,
        original_request=payload.request,
        budget_limit=payload.budget_limit,
        status="queued",
    )

    # Trigger background execution without blocking the HTTP response
    orchestrator = WorkflowOrchestrator()
    background_tasks.add_task(orchestrator.execute_workflow, workflow.id, current_user.id)

    return WorkflowSummaryResponse(
        id=workflow.id,
        user_id=workflow.user_id,
        original_request=workflow.original_request,
        budget_limit=float(workflow.budget_limit) if workflow.budget_limit is not None else None,
        status=workflow.status,
        created_at=workflow.created_at,
        completed_at=workflow.completed_at,
    )


@router.get("", response_model=WorkflowListResponse)
def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists the authenticated user's workflows with pagination (newest first)."""
    wf_repo = WorkflowRepository(db)
    items, total = wf_repo.list_by_user(current_user.id, skip=skip, limit=limit)

    summary_items = [
        WorkflowSummaryResponse(
            id=item.id,
            user_id=item.user_id,
            original_request=item.original_request,
            budget_limit=float(item.budget_limit) if item.budget_limit is not None else None,
            status=item.status,
            created_at=item.created_at,
            completed_at=item.completed_at,
        )
        for item in items
    ]

    return WorkflowListResponse(
        items=summary_items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{workflow_id}", response_model=WorkflowDetailResponse)
def get_workflow(
    workflow_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves full details, plan DAG, and task statuses for a workflow.
    Returns 404 if not found or owned by another user.
    """
    wf_repo = WorkflowRepository(db)
    workflow = wf_repo.get_by_id(workflow_id, current_user.id)
    if not workflow:
        raise ResourceNotFoundError("Workflow not found")

    tasks_data = [
        {
            "id": str(t.id),
            "task_key": t.task_key,
            "description": t.description,
            "tool_name": t.tool_name,
            "status": t.status,
            "result": t.result_json,
            "error_message": t.error_message,
            "started_at": t.started_at.isoformat() if t.started_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        }
        for t in workflow.tasks
    ]

    return WorkflowDetailResponse(
        id=workflow.id,
        user_id=workflow.user_id,
        original_request=workflow.original_request,
        budget_limit=float(workflow.budget_limit) if workflow.budget_limit is not None else None,
        status=workflow.status,
        plan=workflow.plan_json,
        tasks=tasks_data,
        error_message=workflow.error_message,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
        completed_at=workflow.completed_at,
    )


@router.get("/{workflow_id}/report")
def get_workflow_report(
    workflow_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves the final verified report. Returns 409 Conflict if workflow
    is still processing, and 404 if not owned by the user.
    """
    wf_repo = WorkflowRepository(db)
    workflow = wf_repo.get_by_id(workflow_id, current_user.id)
    if not workflow:
        raise ResourceNotFoundError("Workflow not found")

    if workflow.status in ["queued", "planning", "running"] or not workflow.report_json:
        raise WorkflowConflictError(
            f"Workflow report is not ready (current status: '{workflow.status}')"
        )

    return workflow.report_json


@router.post("/{workflow_id}/cancel", response_model=WorkflowSummaryResponse)
def cancel_workflow(
    workflow_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cancels a queued or running workflow. Unstarted tasks are marked cancelled;
    completed tasks retain their results.
    """
    wf_repo = WorkflowRepository(db)
    workflow = wf_repo.get_by_id(workflow_id, current_user.id)
    if not workflow:
        raise ResourceNotFoundError("Workflow not found")

    orchestrator = WorkflowOrchestrator(db=db)
    updated = orchestrator.cancel_workflow(workflow_id, current_user.id)

    return WorkflowSummaryResponse(
        id=updated.id,
        user_id=updated.user_id,
        original_request=updated.original_request,
        budget_limit=float(updated.budget_limit) if updated.budget_limit is not None else None,
        status=updated.status,
        created_at=updated.created_at,
        completed_at=updated.completed_at,
    )
