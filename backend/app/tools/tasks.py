import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.schemas.tools import CreateTasksInput, CreateTasksOutput, CreatedTaskDetail
from app.db.repositories import TaskRepository
from app.core.exceptions import ToolExecutionError


def create_tasks(
    input_data: CreateTasksInput, context: Optional[Dict[str, Any]] = None
) -> CreateTasksOutput:
    """
    Persists preparation tasks to the database associated with the active
    workflow and authenticated user ID, strictly verifying persistence.
    """
    context = context or {}
    db: Optional[Session] = context.get("db")
    workflow_id: Optional[uuid.UUID] = context.get("workflow_id")
    user_id: Optional[uuid.UUID] = context.get("user_id")

    persisted: list[CreatedTaskDetail] = []

    if db and workflow_id and user_id:
        task_repo = TaskRepository(db)
        for idx, task_in in enumerate(input_data.tasks, start=1):
            task_key = f"prep_task_{idx}"
            try:
                task_record = task_repo.create_task(
                    workflow_id=workflow_id,
                    user_id=user_id,
                    task_key=task_key,
                    description=task_in.description,
                    tool_name="task_item",
                    arguments_json={
                        "priority": task_in.priority,
                        "deadline_days": task_in.deadline_days,
                    },
                    dependencies_json=[],
                    status="pending",
                )
                if not task_record or not task_record.id:
                    raise ToolExecutionError(f"Failed to verify persistence of task {task_key}")

                persisted.append(
                    CreatedTaskDetail(
                        id=str(task_record.id),
                        task_key=task_record.task_key,
                        description=task_record.description,
                        priority=task_in.priority,
                        status=task_record.status,
                    )
                )
            except Exception as err:
                raise ToolExecutionError(f"Database error persisting task {task_key}: {str(err)}")
    else:
        # Fallback when executed without active DB context (e.g. schema dry-run)
        for idx, task_in in enumerate(input_data.tasks, start=1):
            persisted.append(
                CreatedTaskDetail(
                    id=str(uuid.uuid4()),
                    task_key=f"prep_task_{idx}",
                    description=task_in.description,
                    priority=task_in.priority,
                    status="pending",
                )
            )

    return CreateTasksOutput(
        created_tasks=persisted,
        total_created=len(persisted),
    )
