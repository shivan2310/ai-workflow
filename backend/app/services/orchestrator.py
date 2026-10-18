import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Workflow, WorkflowTask
from app.db.repositories import WorkflowRepository, TaskRepository, ExecutionRepository
from app.schemas.plan import WorkflowPlan
from app.services.planner import CloudPlannerService
from app.services.verifier import ResultVerifier
from app.services.report_service import ReportService
from app.tools.registry import default_tool_registry
from app.core.exceptions import ToolExecutionError, PlanValidationError

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowOrchestrator:
    def __init__(self, db: Optional[Session] = None):
        self._db = db
        self.planner = CloudPlannerService()

    def _get_db(self) -> Session:
        if self._db:
            return self._db
        return SessionLocal()

    async def execute_workflow(self, workflow_id: uuid.UUID, user_id: uuid.UUID) -> Workflow:
        """
        Drives the end-to-end execution of a workflow:
        1. Planning via CloudPlannerService
        2. Task persistence in pending state
        3. Topological DAG execution
        4. Cascading error blocking
        5. Verification and final report assembly
        """
        db = self._get_db()
        wf_repo = WorkflowRepository(db)
        task_repo = TaskRepository(db)
        exec_repo = ExecutionRepository(db)

        workflow = wf_repo.get_by_id(workflow_id, user_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found for user {user_id}")
            return None

        # 1. Planning stage
        wf_repo.update_status(workflow_id, user_id, status="planning")
        try:
            plan: WorkflowPlan = await self.planner.plan(
                user_request=workflow.original_request,
                budget_limit=float(workflow.budget_limit) if workflow.budget_limit is not None else None,
            )
            wf_repo.update_status(
                workflow_id, user_id, status="planning", plan_json=plan.model_dump(mode="json")
            )
        except Exception as plan_err:
            error_msg = f"Planning failed: {str(plan_err)}"
            logger.error(error_msg)
            wf_repo.update_status(
                workflow_id,
                user_id,
                status="failed",
                error_message=error_msg,
                completed_at=utc_now(),
            )
            return wf_repo.get_by_id(workflow_id, user_id)

        # 2. Persist tasks in DB
        created_tasks: Dict[str, WorkflowTask] = {}
        for item in plan.tasks:
            task_rec = task_repo.create_task(
                workflow_id=workflow_id,
                user_id=user_id,
                task_key=item.task_key,
                description=item.description,
                tool_name=item.tool_name,
                arguments_json=item.arguments,
                dependencies_json=item.dependencies,
                status="pending",
            )
            created_tasks[item.task_key] = task_rec

        # 3. Transition to running
        wf_repo.update_status(workflow_id, user_id, status="running")

        # 4. Topological execution loop
        completed_keys = set()
        failed_or_blocked_keys = set()
        remaining_tasks = list(plan.tasks)

        # Map to find who depends on a task
        while remaining_tasks:
            # Check if workflow was cancelled mid-execution
            current_wf = wf_repo.get_by_id(workflow_id, user_id)
            if current_wf and current_wf.status == "cancelled":
                for rem in remaining_tasks:
                    task_rec = created_tasks[rem.task_key]
                    task_repo.update_status(task_rec.id, user_id, status="cancelled")
                break

            # Find ready tasks (all dependencies in completed_keys)
            ready_tasks = [
                t for t in remaining_tasks
                if all(dep in completed_keys for dep in t.dependencies)
            ]

            # If no tasks are ready but remaining exist, check if dependencies failed
            if not ready_tasks:
                blocked_candidates = [
                    t for t in remaining_tasks
                    if any(dep in failed_or_blocked_keys for dep in t.dependencies)
                ]
                if blocked_candidates:
                    for blocked in blocked_candidates:
                        task_rec = created_tasks[blocked.task_key]
                        task_repo.update_status(
                            task_rec.id,
                            user_id,
                            status="blocked",
                            error_message="Blocked due to failed or blocked prerequisite task",
                        )
                        failed_or_blocked_keys.add(blocked.task_key)
                        remaining_tasks.remove(blocked)
                    continue
                else:
                    # Deadlock or unresolvable state
                    break

            # Execute the first ready task
            task_item = ready_tasks[0]
            remaining_tasks.remove(task_item)
            task_rec = created_tasks[task_item.task_key]

            # Mark task running
            task_repo.update_status(
                task_rec.id, user_id, status="running", started_at=utc_now()
            )

            # Record tool execution start
            execution = exec_repo.record_start(
                workflow_id=workflow_id,
                workflow_task_id=task_rec.id,
                user_id=user_id,
                tool_name=task_item.tool_name,
                input_json=task_item.arguments,
            )

            # Execute tool
            try:
                context = {
                    "db": db,
                    "workflow_id": workflow_id,
                    "user_id": user_id,
                }
                output_model = default_tool_registry.execute(
                    name=task_item.tool_name,
                    arguments=task_item.arguments,
                    context=context,
                )
                output_dict = output_model.model_dump(mode="json")

                # Record execution success
                exec_repo.record_finish(
                    execution_id=execution.id,
                    status="completed",
                    output_json=output_dict,
                )

                # Mark task completed
                task_repo.update_status(
                    task_id=task_rec.id,
                    user_id=user_id,
                    status="completed",
                    result_json=output_dict,
                    completed_at=utc_now(),
                )
                completed_keys.add(task_item.task_key)

            except Exception as tool_err:
                err_str = str(tool_err)
                logger.warning(f"Task '{task_item.task_key}' failed: {err_str}")

                # Record execution failure
                exec_repo.record_finish(
                    execution_id=execution.id,
                    status="failed",
                    error_message=err_str,
                )

                # Mark task failed
                task_repo.update_status(
                    task_id=task_rec.id,
                    user_id=user_id,
                    status="failed",
                    error_message=err_str,
                    completed_at=utc_now(),
                )
                failed_or_blocked_keys.add(task_item.task_key)

                # Cascade block all dependent tasks in remaining_tasks
                def cascade_block(failed_key: str):
                    for other in list(remaining_tasks):
                        if failed_key in other.dependencies:
                            other_rec = created_tasks[other.task_key]
                            task_repo.update_status(
                                other_rec.id,
                                user_id,
                                status="blocked",
                                error_message=f"Blocked: prerequisite '{failed_key}' failed",
                                completed_at=utc_now(),
                            )
                            failed_or_blocked_keys.add(other.task_key)
                            remaining_tasks.remove(other)
                            cascade_block(other.task_key)

                cascade_block(task_item.task_key)

        # 5. Result Verification & Final Report Generation
        tasks_list, _ = task_repo.list_by_user(user_id=user_id, workflow_id=workflow_id)
        current_wf = wf_repo.get_by_id(workflow_id, user_id)

        if current_wf.status != "cancelled":
            verification = ResultVerifier.verify(current_wf, tasks_list)
            report = ReportService.build_report(current_wf, tasks_list, verification)

            terminal_status = "completed" if verification["outcome"] == "success" else "failed"
            wf_repo.update_status(
                workflow_id=workflow_id,
                user_id=user_id,
                status=terminal_status,
                report_json=report,
                completed_at=utc_now(),
            )

        return wf_repo.get_by_id(workflow_id, user_id)

    def cancel_workflow(self, workflow_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Workflow]:
        """
        Safely cancels a queued or running workflow.
        Tasks that have not yet run are marked cancelled.
        Completed tasks retain their persisted results.
        """
        db = self._get_db()
        wf_repo = WorkflowRepository(db)
        task_repo = TaskRepository(db)

        workflow = wf_repo.get_by_id(workflow_id, user_id)
        if not workflow:
            return None

        if workflow.status in ["completed", "failed", "cancelled"]:
            return workflow

        # Mark unstarted tasks as cancelled
        tasks, _ = task_repo.list_by_user(user_id, workflow_id)
        for t in tasks:
            if t.status in ["pending", "running"]:
                task_repo.update_status(t.id, user_id, status="cancelled")

        # Update workflow status to cancelled
        updated = wf_repo.update_status(
            workflow_id=workflow_id,
            user_id=user_id,
            status="cancelled",
            completed_at=utc_now(),
        )
        return updated
