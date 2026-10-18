import uuid
import time
import pytest
import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import Base, get_db
from app.db.repositories import WorkflowRepository, TaskRepository
from app.core.config import get_settings

TEST_JWT_SECRET = "super-secret-test-key-32-bytes-long!"


from sqlalchemy.pool import StaticPool
import app.db.database as db_module

@pytest.fixture
def test_db_session(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr(db_module, "SessionLocal", TestingSession)

    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db_session, monkeypatch):
    monkeypatch.setattr(get_settings(), "SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setattr(get_settings(), "SUPABASE_JWT_AUDIENCE", "authenticated")

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_token(user_id: uuid.UUID) -> str:
    payload = {
        "sub": str(user_id),
        "email": f"user-{str(user_id)[:8]}@innotech.org",
        "role": "authenticated",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["connected"] is True
    assert data["llm"]["provider"] == "cloud"


def test_unauthenticated_request_rejected(client):
    response = client.post("/api/workflows", json={"request": "Workshop organization"})
    assert response.status_code == 401
    assert "Authorization Bearer token is required" in response.json()["error"]


def test_invalid_token_rejected(client):
    response = client.get(
        "/api/workflows",
        headers={"Authorization": "Bearer invalid-garbage-token"},
    )
    assert response.status_code == 401


def test_create_workflow_authenticated(client):
    user_id = uuid.uuid4()
    token = make_token(user_id)

    response = client.post(
        "/api/workflows",
        json={
            "request": "Organize technical workshop for 100 students",
            "budget_limit": 20000.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["user_id"] == str(user_id)
    assert data["status"] == "queued"
    assert data["budget_limit"] == 20000.0


def test_list_workflows_and_user_isolation(client, test_db_session):
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()

    token_a = make_token(user_a)
    token_b = make_token(user_b)

    wf_repo = WorkflowRepository(test_db_session)
    wf_a = wf_repo.create(user_id=user_a, original_request="User A workshop")
    wf_b = wf_repo.create(user_id=user_b, original_request="User B workshop")

    # User A requests workflows
    res_a = client.get("/api/workflows", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["total"] == 1
    assert data_a["items"][0]["id"] == str(wf_a.id)

    # User B requests workflows
    res_b = client.get("/api/workflows", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["total"] == 1
    assert data_b["items"][0]["id"] == str(wf_b.id)


def test_get_workflow_by_id_and_cross_user_prevention(client, test_db_session):
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()

    token_a = make_token(user_a)
    token_b = make_token(user_b)

    wf_repo = WorkflowRepository(test_db_session)
    wf_a = wf_repo.create(user_id=user_a, original_request="User A private workflow")

    # Owner can retrieve
    res_owner = client.get(
        f"/api/workflows/{wf_a.id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_owner.status_code == 200
    assert res_owner.json()["id"] == str(wf_a.id)

    # Other user CANNOT retrieve (returns 404, never 200 or foreign data)
    res_foreign = client.get(
        f"/api/workflows/{wf_a.id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_foreign.status_code == 404
    assert "Workflow not found" in res_foreign.json()["error"]


def test_get_workflow_report_lifecycle(client, test_db_session):
    user_id = uuid.uuid4()
    token = make_token(user_id)

    wf_repo = WorkflowRepository(test_db_session)
    wf = wf_repo.create(user_id=user_id, original_request="Report test")

    # While running/queued, report returns 409 Conflict
    res_conflict = client.get(
        f"/api/workflows/{wf.id}/report",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_conflict.status_code == 409
    assert "not ready" in res_conflict.json()["error"]

    # When completed with report_json, returns report
    wf_repo.update_status(
        workflow_id=wf.id,
        user_id=user_id,
        status="completed",
        report_json={
            "outcome": "success",
            "budget_verification": {"total_cost": 18000},
        },
    )

    res_ok = client.get(
        f"/api/workflows/{wf.id}/report",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["outcome"] == "success"


def test_cancel_workflow(client, test_db_session):
    user_id = uuid.uuid4()
    token = make_token(user_id)

    wf_repo = WorkflowRepository(test_db_session)
    wf = wf_repo.create(user_id=user_id, original_request="Cancel test")

    response = client.post(
        f"/api/workflows/{wf.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_list_tasks_by_user(client, test_db_session):
    user_id = uuid.uuid4()
    token = make_token(user_id)

    wf_repo = WorkflowRepository(test_db_session)
    task_repo = TaskRepository(test_db_session)

    wf = wf_repo.create(user_id=user_id, original_request="Task list test")
    t1 = task_repo.create_task(
        workflow_id=wf.id,
        user_id=user_id,
        task_key="t_1",
        description="Book room",
        tool_name="task_item",
        arguments_json={},
        dependencies_json=[],
    )

    res = client.get("/api/tasks", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["task_key"] == "t_1"
