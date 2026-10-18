import uuid
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db.repositories import WorkflowRepository, TaskRepository
from app.services.orchestrator import WorkflowOrchestrator
from app.schemas.plan import WorkflowPlan, TaskPlanItem


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_orchestrator_successful_execution(test_db):
    wf_repo = WorkflowRepository(test_db)
    user_id = uuid.uuid4()

    wf = wf_repo.create(
        user_id=user_id,
        original_request="Organize workshop for 100 students within ₹20,000",
        budget_limit=20000.0,
    )

    orchestrator = WorkflowOrchestrator(db=test_db)
    completed_wf = await orchestrator.execute_workflow(wf.id, user_id)

    assert completed_wf is not None
    assert completed_wf.status == "completed"
    assert completed_wf.report_json is not None
    assert completed_wf.report_json["outcome"] == "success"

    # Verify tasks
    task_repo = TaskRepository(test_db)
    tasks, count = task_repo.list_by_user(user_id, wf.id)
    assert count == 6  # 3 plan tasks + 3 generated preparation tasks
    plan_tasks = [t for t in tasks if t.tool_name != "task_item"]
    assert len(plan_tasks) == 3
    for t in plan_tasks:
        assert t.status == "completed"
        assert t.result_json is not None

    # Check budget verification
    budget_verification = completed_wf.report_json["budget_verification"]
    assert budget_verification["verified_by"] == "python_deterministic_engine"
    assert budget_verification["total_cost"] == 18000.0
    assert budget_verification["budget_limit"] == 20000.0
    assert budget_verification["is_within_budget"] is True


@pytest.mark.asyncio
async def test_orchestrator_cascading_failure_and_blocking(test_db):
    wf_repo = WorkflowRepository(test_db)
    task_repo = TaskRepository(test_db)
    user_id = uuid.uuid4()

    wf = wf_repo.create(
        user_id=user_id,
        original_request="Workshop with failing task",
    )

    # Custom plan where task_1 fails, and task_2 depends on task_1
    bad_plan = WorkflowPlan(
        goal="Test failure cascade",
        tasks=[
            TaskPlanItem(
                task_key="task_1",
                description="This tool will fail",
                tool_name="calculate_budget",
                arguments={
                    "items": [{"name": "Item", "amount": 100}],
                    "budget_limit": 200,
                },
                dependencies=[],
            ),
            TaskPlanItem(
                task_key="task_2",
                description="Should be blocked",
                tool_name="draft_email",
                arguments={
                    "purpose": "Workshop",
                    "intended_audience": "Students",
                },
                dependencies=["task_1"],
            ),
        ],
    )

    orchestrator = WorkflowOrchestrator(db=test_db)

    # Force task_1 to fail during execution
    with patch("app.tools.registry.ToolRegistry.execute") as mock_exec:
        mock_exec.side_effect = RuntimeError("Simulated tool execution crash")
        with patch.object(orchestrator.planner, "plan", return_value=bad_plan):
            failed_wf = await orchestrator.execute_workflow(wf.id, user_id)

    assert failed_wf.status == "failed"
    assert failed_wf.report_json["outcome"] == "failed"

    tasks, _ = task_repo.list_by_user(user_id, wf.id)
    task_map = {t.task_key: t for t in tasks}

    # task_1 failed
    assert task_map["task_1"].status == "failed"
    assert "Simulated tool execution crash" in task_map["task_1"].error_message

    # task_2 blocked due to prerequisite failure
    assert task_map["task_2"].status == "blocked"
    assert "Blocked" in task_map["task_2"].error_message


@pytest.mark.asyncio
async def test_orchestrator_cancel_workflow(test_db):
    wf_repo = WorkflowRepository(test_db)
    task_repo = TaskRepository(test_db)
    user_id = uuid.uuid4()

    wf = wf_repo.create(user_id=user_id, original_request="To be cancelled")
    t1 = task_repo.create_task(
        workflow_id=wf.id,
        user_id=user_id,
        task_key="task_1",
        description="Pending task",
        tool_name="calculate_budget",
        arguments_json={},
        dependencies_json=[],
        status="pending",
    )

    orchestrator = WorkflowOrchestrator(db=test_db)
    cancelled = orchestrator.cancel_workflow(wf.id, user_id)

    assert cancelled.status == "cancelled"
    updated_t1 = task_repo.list_by_user(user_id, wf.id)[0][0]
    assert updated_t1.status == "cancelled"
