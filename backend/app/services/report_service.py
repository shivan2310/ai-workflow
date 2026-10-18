from typing import Dict, Any, List
from datetime import datetime, timezone
from app.db.models import Workflow, WorkflowTask


class ReportService:
    @staticmethod
    def build_report(
        workflow: Workflow,
        tasks: List[WorkflowTask],
        verification: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Synthesizes verified task executions and audit checks into a
        transparent, user-facing final report.
        """
        task_details = [
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
            for t in tasks
        ]

        completed_iso = None
        if workflow.completed_at:
            completed_iso = workflow.completed_at.isoformat()
        else:
            completed_iso = datetime.now(timezone.utc).isoformat()

        return {
            "workflow_id": str(workflow.id),
            "status": workflow.status,
            "original_request": workflow.original_request,
            "budget_limit": float(workflow.budget_limit) if workflow.budget_limit is not None else None,
            "summary": verification.get("summary", {}),
            "outcome": verification.get("outcome", "unknown"),
            "budget_verification": verification.get("budget_verification", {}),
            "tasks_persisted": verification.get("tasks_persisted", 0),
            "email_draft": verification.get("email_draft", {}),
            "executed_tasks": task_details,
            "completed_at": completed_iso,
        }
