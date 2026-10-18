import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db.repositories import WorkflowRepository, TaskRepository, ExecutionRepository


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_workflow_repository_crud_and_isolation(db_session):
    repo = WorkflowRepository(db_session)
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()

    # User A creates a workflow
    wf_a = repo.create(
        user_id=user_a,
        original_request="Organize workshop for 100 students",
        budget_limit=20000.0,
    )
    assert wf_a.id is not None
    assert wf_a.status == "queued"
    assert wf_a.user_id == user_a

    # User A can retrieve it
    retrieved = repo.get_by_id(wf_a.id, user_id=user_a)
    assert retrieved is not None
    assert retrieved.original_request == "Organize workshop for 100 students"

    # User B CANNOT retrieve User A's workflow (User isolation check)
    foreign = repo.get_by_id(wf_a.id, user_id=user_b)
    assert foreign is None

    # Update workflow
    updated = repo.update_status(
        workflow_id=wf_a.id,
        user_id=user_a,
        status="running",
        plan_json={"goal": "test plan"},
    )
    assert updated.status == "running"
    assert updated.plan_json == {"goal": "test plan"}

    # User B cannot update User A's workflow
    foreign_update = repo.update_status(
        workflow_id=wf_a.id,
        user_id=user_b,
        status="cancelled",
    )
    assert foreign_update is None

    # Listing returns only User A's workflows
    items, total = repo.list_by_user(user_id=user_a)
    assert total == 1
    assert items[0].id == wf_a.id

    b_items, b_total = repo.list_by_user(user_id=user_b)
    assert b_total == 0
    assert len(b_items) == 0


def test_task_repository_and_cascade(db_session):
    wf_repo = WorkflowRepository(db_session)
    task_repo = TaskRepository(db_session)
    user_id = uuid.uuid4()

    wf = wf_repo.create(
        user_id=user_id,
        original_request="Test task workflow",
    )

    t1 = task_repo.create_task(
        workflow_id=wf.id,
        user_id=user_id,
        task_key="task_1",
        description="Calculate workshop budget",
        tool_name="calculate_budget",
        arguments_json={"limit": 20000},
        dependencies_json=[],
    )
    assert t1.id is not None
    assert t1.task_key == "task_1"
    assert t1.status == "pending"

    # Update task
    updated = task_repo.update_status(
        task_id=t1.id,
        user_id=user_id,
        status="completed",
        result_json={"total": 18000},
    )
    assert updated.status == "completed"
    assert updated.result_json == {"total": 18000}
    assert updated.completed_at is not None

    # List tasks
    tasks, count = task_repo.list_by_user(user_id=user_id, workflow_id=wf.id)
    assert count == 1
    assert tasks[0].task_key == "task_1"


def test_execution_repository(db_session):
    wf_repo = WorkflowRepository(db_session)
    exec_repo = ExecutionRepository(db_session)
    user_id = uuid.uuid4()

    wf = wf_repo.create(user_id=user_id, original_request="Execution test")
    execution = exec_repo.record_start(
        workflow_id=wf.id,
        user_id=user_id,
        tool_name="calculate_budget",
        input_json={"amount": 100},
    )
    assert execution.status == "running"

    finished = exec_repo.record_finish(
        execution_id=execution.id,
        status="completed",
        output_json={"result": "ok"},
    )
    assert finished.status == "completed"
    assert finished.output_json == {"result": "ok"}
    assert finished.completed_at is not None
