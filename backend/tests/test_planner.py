import pytest
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError
import httpx
from app.schemas.plan import WorkflowPlan, TaskPlanItem
from app.services.planner import CloudPlannerService, generate_fallback_workshop_plan
from app.core.exceptions import CloudLLMError, PlanValidationError
from app.core.config import get_settings


def test_valid_dag_plan():
    plan = WorkflowPlan(
        goal="Organize workshop for 100 students",
        tasks=[
            TaskPlanItem(
                task_key="task_1",
                description="Budget check",
                tool_name="calculate_budget",
                arguments={
                    "items": [{"name": "Snacks", "amount": 5000}],
                    "budget_limit": 20000,
                },
                dependencies=[],
            ),
            TaskPlanItem(
                task_key="task_2",
                description="Draft email",
                tool_name="draft_email",
                arguments={
                    "purpose": "Workshop Organization",
                    "intended_audience": "Students",
                },
                dependencies=["task_1"],
            ),
        ],
    )
    assert len(plan.tasks) == 2
    assert plan.tasks[0].task_key == "task_1"


def test_circular_dependency_rejection():
    with pytest.raises(ValidationError, match="Circular dependency detected"):
        WorkflowPlan(
            goal="Circular plan",
            tasks=[
                TaskPlanItem(
                    task_key="task_1",
                    description="Step 1",
                    tool_name="draft_email",
                    arguments={"purpose": "Plan Phase 1", "intended_audience": "Audience 1"},
                    dependencies=["task_2"],
                ),
                TaskPlanItem(
                    task_key="task_2",
                    description="Step 2",
                    tool_name="draft_email",
                    arguments={"purpose": "Plan Phase 2", "intended_audience": "Audience 2"},
                    dependencies=["task_1"],
                ),
            ],
        )


def test_missing_dependency_rejection():
    with pytest.raises(ValidationError, match="non-existent task 'task_99'"):
        WorkflowPlan(
            goal="Broken plan",
            tasks=[
                TaskPlanItem(
                    task_key="task_1",
                    description="Step 1",
                    tool_name="draft_email",
                    arguments={"purpose": "Valid Purpose", "intended_audience": "Valid Audience"},
                    dependencies=["task_99"],
                ),
            ],
        )


def test_unknown_tool_rejection():
    with pytest.raises(ValidationError, match="Unknown tool name 'unregistered_hack'"):
        WorkflowPlan(
            goal="Malicious plan",
            tasks=[
                TaskPlanItem(
                    task_key="task_1",
                    description="Step 1",
                    tool_name="unregistered_hack",
                    arguments={},
                    dependencies=[],
                ),
            ],
        )


def test_invalid_tool_argument_rejection():
    with pytest.raises(ValidationError, match="do not match tool 'calculate_budget'"):
        WorkflowPlan(
            goal="Bad args plan",
            tasks=[
                TaskPlanItem(
                    task_key="task_1",
                    description="Budget",
                    tool_name="calculate_budget",
                    arguments={"items": "not-a-list"},  # Invalid
                    dependencies=[],
                ),
            ],
        )


def test_fallback_workshop_plan():
    plan = generate_fallback_workshop_plan("Technical AI workshop", budget_limit=25000.0)
    assert len(plan.tasks) == 3
    assert plan.tasks[0].tool_name == "calculate_budget"
    assert plan.tasks[0].arguments["budget_limit"] == 25000.0
    assert plan.tasks[1].dependencies == ["task_1"]
    assert plan.tasks[2].dependencies == ["task_1"]


@pytest.mark.asyncio
async def test_cloud_planner_fallback_when_no_api_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "LLM_API_KEY", None)
    planner = CloudPlannerService()
    plan = await planner.plan("Host a cloud hackathon", budget_limit=15000.0)
    assert plan.goal is not None
    assert len(plan.tasks) == 3


@pytest.mark.asyncio
async def test_cloud_planner_mocked_cloud_call(monkeypatch):
    monkeypatch.setattr(get_settings(), "LLM_API_KEY", "real-cloud-api-key-12345")
    planner = CloudPlannerService()

    mock_response_data = {
        "choices": [
            {
                "message": {
                    "content": """{
                        "goal": "Organize AI Symposium",
                        "tasks": [
                            {
                                "task_key": "task_1",
                                "description": "Calculate costs",
                                "tool_name": "calculate_budget",
                                "arguments": {
                                    "items": [{"name": "Lunch", "amount": 5000}],
                                    "budget_limit": 20000
                                },
                                "dependencies": []
                            }
                        ]
                    }"""
                }
            }
        ]
    }

    mock_resp = httpx.Response(200, json=mock_response_data, request=httpx.Request("POST", "http://test"))

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        plan = await planner.plan("Organize AI Symposium", budget_limit=20000)

        assert plan.goal == "Organize AI Symposium"
        assert len(plan.tasks) == 1
        assert plan.tasks[0].task_key == "task_1"
