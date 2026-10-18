import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WorkflowCreateRequest(BaseModel):
    request: str = Field(min_length=5, max_length=1000, description="Natural language workflow goal")
    budget_limit: Optional[float] = Field(default=None, ge=0, description="Optional budget limit ceiling")


class WorkflowSummaryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    original_request: str
    budget_limit: Optional[float] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None


class WorkflowDetailResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    original_request: str
    budget_limit: Optional[float] = None
    status: str
    plan: Optional[Dict[str, Any]] = None
    tasks: List[Dict[str, Any]] = []
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class WorkflowListResponse(BaseModel):
    items: List[WorkflowSummaryResponse]
    total: int
    skip: int
    limit: int


class TaskDetailResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    task_key: str
    description: str
    tool_name: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskListResponse(BaseModel):
    items: List[TaskDetailResponse]
    total: int
    skip: int
    limit: int
