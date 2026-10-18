import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, selectinload
from app.db.models import Workflow, WorkflowTask, ToolExecution


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: uuid.UUID,
        original_request: str,
        budget_limit: Optional[float] = None,
        status: str = "queued",
    ) -> Workflow:
        workflow = Workflow(
            user_id=user_id,
            original_request=original_request,
            budget_limit=budget_limit,
            status=status,
        )
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def get_by_id(
        self, workflow_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Workflow]:
        """Fetch workflow by ID enforcing user ownership with eager loading of tasks."""
        stmt = (
            select(Workflow)
            .where(
                and_(
                    Workflow.id == workflow_id,
                    Workflow.user_id == user_id,
                )
            )
            .options(selectinload(Workflow.tasks))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Workflow], int]:
        """List user's workflows ordered newest first with total count."""
        count_stmt = (
            select(func.count(Workflow.id)).where(Workflow.user_id == user_id)
        )
        total = self.db.execute(count_stmt).scalar() or 0

        stmt = (
            select(Workflow)
            .where(Workflow.user_id == user_id)
            .order_by(Workflow.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def update_status(
        self,
        workflow_id: uuid.UUID,
        user_id: uuid.UUID,
        status: str,
        plan_json: Optional[Dict[str, Any]] = None,
        report_json: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[Workflow]:
        workflow = self.get_by_id(workflow_id, user_id)
        if not workflow:
            return None

        workflow.status = status
        if plan_json is not None:
            workflow.plan_json = plan_json
        if report_json is not None:
            workflow.report_json = report_json
        if error_message is not None:
            workflow.error_message = error_message
        if completed_at is not None:
            workflow.completed_at = completed_at
        elif status in ["completed", "failed", "cancelled"] and not workflow.completed_at:
            workflow.completed_at = utc_now()

        self.db.commit()
        self.db.refresh(workflow)
        return workflow


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_task(
        self,
        workflow_id: uuid.UUID,
        user_id: uuid.UUID,
        task_key: str,
        description: str,
        tool_name: str,
        arguments_json: Dict[str, Any],
        dependencies_json: List[str],
        status: str = "pending",
    ) -> WorkflowTask:
        task = WorkflowTask(
            workflow_id=workflow_id,
            user_id=user_id,
            task_key=task_key,
            description=description,
            tool_name=tool_name,
            arguments_json=arguments_json,
            dependencies_json=dependencies_json,
            status=status,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def list_by_user(
        self,
        user_id: uuid.UUID,
        workflow_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[WorkflowTask], int]:
        conditions = [WorkflowTask.user_id == user_id]
        if workflow_id:
            conditions.append(WorkflowTask.workflow_id == workflow_id)

        count_stmt = select(func.count(WorkflowTask.id)).where(and_(*conditions))
        total = self.db.execute(count_stmt).scalar() or 0

        stmt = (
            select(WorkflowTask)
            .where(and_(*conditions))
            .order_by(WorkflowTask.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        tasks = list(self.db.execute(stmt).scalars().all())
        return tasks, total

    def update_status(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        status: str,
        result_json: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[WorkflowTask]:
        stmt = select(WorkflowTask).where(
            and_(WorkflowTask.id == task_id, WorkflowTask.user_id == user_id)
        )
        task = self.db.execute(stmt).scalar_one_or_none()
        if not task:
            return None

        task.status = status
        if result_json is not None:
            task.result_json = result_json
        if error_message is not None:
            task.error_message = error_message
        if started_at is not None:
            task.started_at = started_at
        if completed_at is not None:
            task.completed_at = completed_at
        elif status in ["completed", "failed", "blocked", "cancelled"] and not task.completed_at:
            task.completed_at = utc_now()

        self.db.commit()
        self.db.refresh(task)
        return task


class ExecutionRepository:
    def __init__(self, db: Session):
        self.db = db

    def record_start(
        self,
        workflow_id: uuid.UUID,
        user_id: uuid.UUID,
        tool_name: str,
        input_json: Dict[str, Any],
        workflow_task_id: Optional[uuid.UUID] = None,
    ) -> ToolExecution:
        execution = ToolExecution(
            workflow_id=workflow_id,
            workflow_task_id=workflow_task_id,
            user_id=user_id,
            tool_name=tool_name,
            status="running",
            input_json=input_json,
            started_at=utc_now(),
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def record_finish(
        self,
        execution_id: uuid.UUID,
        status: str,
        output_json: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> Optional[ToolExecution]:
        stmt = select(ToolExecution).where(ToolExecution.id == execution_id)
        execution = self.db.execute(stmt).scalar_one_or_none()
        if not execution:
            return None

        execution.status = status
        execution.output_json = output_json
        execution.error_message = error_message
        execution.completed_at = utc_now()

        self.db.commit()
        self.db.refresh(execution)
        return execution
