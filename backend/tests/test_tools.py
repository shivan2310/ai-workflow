import uuid
from decimal import Decimal
import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db.repositories import WorkflowRepository
from app.tools.registry import default_tool_registry
from app.schemas.tools import (
    BudgetItem,
    CalculateBudgetInput,
    CreateTasksInput,
    TaskItemInput,
    DraftEmailInput,
)
from app.tools.budget import calculate_budget
from app.tools.tasks import create_tasks
from app.tools.email_drafter import draft_email
from app.core.exceptions import ToolExecutionError, PlanValidationError


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


def test_calculate_budget_within_limit():
    data = CalculateBudgetInput(
        items=[
            BudgetItem(name="Hall Rental", amount=Decimal("7500.00")),
            BudgetItem(name="Catering", amount=Decimal("6000.50")),
            BudgetItem(name="Certificates", amount=Decimal("1499.50")),
        ],
        budget_limit=Decimal("20000.00"),
    )
    result = calculate_budget(data)

    assert result.total_estimated_cost == Decimal("15000.00")
    assert result.budget_limit == Decimal("20000.00")
    assert result.remaining_amount == Decimal("5000.00")
    assert result.overrun_amount == Decimal("0.00")
    assert result.is_within_budget is True


def test_calculate_budget_overrun():
    data = CalculateBudgetInput(
        items=[
            BudgetItem(name="Expensive Venue", amount=Decimal("15000.00")),
            BudgetItem(name="Catering", amount=Decimal("8000.00")),
        ],
        budget_limit=Decimal("20000.00"),
    )
    result = calculate_budget(data)

    assert result.total_estimated_cost == Decimal("23000.00")
    assert result.remaining_amount == Decimal("0.00")
    assert result.overrun_amount == Decimal("3000.00")
    assert result.is_within_budget is False


def test_calculate_budget_negative_amount_rejected():
    with pytest.raises(ValidationError):
        BudgetItem(name="Negative Item", amount=Decimal("-500.00"))


def test_create_tasks_with_persistence(db_session):
    wf_repo = WorkflowRepository(db_session)
    user_id = uuid.uuid4()
    wf = wf_repo.create(user_id=user_id, original_request="Workshop preparation")

    data = CreateTasksInput(
        tasks=[
            TaskItemInput(description="Book lecture auditorium", priority="high", deadline_days=3),
            TaskItemInput(description="Order refreshments for 100 students", priority="medium", deadline_days=5),
            TaskItemInput(description="Print participant badges", priority="low", deadline_days=7),
        ]
    )

    context = {
        "db": db_session,
        "workflow_id": wf.id,
        "user_id": user_id,
    }

    result = create_tasks(data, context=context)

    assert result.total_created == 3
    assert len(result.created_tasks) == 3
    assert result.created_tasks[0].task_key == "prep_task_1"
    assert result.created_tasks[0].description == "Book lecture auditorium"


def test_draft_email_with_and_without_details():
    # Omit date, venue, and speaker to verify missing detection
    data = DraftEmailInput(
        purpose="Hands-on AI Automation Workshop",
        intended_audience="Engineering Students",
        known_event_details={},
    )
    result = draft_email(data)

    assert "Invitation: Hands-on AI Automation Workshop" in result.subject
    assert result.is_draft_only is True
    assert "Date & Time" in result.missing_information
    assert "Venue / Room Location" in result.missing_information
    assert "[Venue / Room Location: To be announced]" in result.body

    # Provide known details
    detailed_data = DraftEmailInput(
        purpose="Hands-on AI Automation Workshop",
        intended_audience="Engineering Students",
        known_event_details={
            "topic": "Agentic AI with Qwen and GPT",
            "date": "Nov 15, 2026 at 10:00 AM",
            "venue": "Auditorium Hall B",
            "speaker": "Dr. Sarah Chen",
            "registration_deadline": "Nov 10, 2026",
        },
    )
    detailed_result = draft_email(detailed_data)
    assert len(detailed_result.missing_information) == 0
    assert "Auditorium Hall B" in detailed_result.body
    assert "Dr. Sarah Chen" in detailed_result.body


def test_registry_execution_and_validation():
    # Valid call through registry
    args = {
        "items": [
            {"name": "Badges", "amount": "500.00"},
            {"name": "Notebooks", "amount": "1000.00"},
        ],
        "budget_limit": "2000.00",
    }
    output = default_tool_registry.execute("calculate_budget", args)
    assert output.total_estimated_cost == Decimal("1500.00")
    assert output.is_within_budget is True

    # Unknown tool rejection
    with pytest.raises(ToolExecutionError, match="unregistered tool"):
        default_tool_registry.execute("delete_user_account", {})

    # Invalid argument schema rejection
    with pytest.raises(PlanValidationError, match="Invalid arguments"):
        default_tool_registry.execute("calculate_budget", {"items": []})  # items min_length=1
