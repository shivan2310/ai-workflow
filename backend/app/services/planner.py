import json
import logging
from typing import Optional, Dict, Any
import httpx
from pydantic import ValidationError
from app.core.config import get_settings
from app.core.exceptions import CloudLLMError, PlanValidationError
from app.schemas.plan import WorkflowPlan, TaskPlanItem
from app.tools.registry import default_tool_registry

logger = logging.getLogger(__name__)


def generate_fallback_workshop_plan(
    request: str, budget_limit: Optional[float] = None
) -> WorkflowPlan:
    """
    Deterministic fallback plan for testing, offline environments, or when
    cloud API credentials are not yet configured.
    """
    limit = budget_limit if budget_limit is not None else 20000.00
    return WorkflowPlan(
        goal=f"Organize Technical Workshop: {request}",
        tasks=[
            TaskPlanItem(
                task_key="task_1",
                description="Calculate and verify itemized workshop budget against ceiling limit",
                tool_name="calculate_budget",
                arguments={
                    "items": [
                        {"name": "Venue & Projector Rental", "amount": 8000.00},
                        {"name": "Refreshments & Snacks (100 students)", "amount": 7500.00},
                        {"name": "Certificates, Badges & Kits", "amount": 2500.00},
                    ],
                    "budget_limit": limit,
                },
                dependencies=[],
                expected_output="Itemized breakdown and budget ceiling verification result",
                completion_criteria="Total calculated within budget ceiling",
            ),
            TaskPlanItem(
                task_key="task_2",
                description="Create and persist operational preparation checklist tasks",
                tool_name="create_tasks",
                arguments={
                    "tasks": [
                        {
                            "description": "Reserve auditorium and test audiovisual equipment",
                            "priority": "high",
                            "deadline_days": 4,
                        },
                        {
                            "description": "Finalize catering order for 100 student participants",
                            "priority": "high",
                            "deadline_days": 3,
                        },
                        {
                            "description": "Design and print certificates of participation",
                            "priority": "medium",
                            "deadline_days": 7,
                        },
                    ]
                },
                dependencies=["task_1"],
                expected_output="Persisted task checklist records in database",
                completion_criteria="Task IDs generated and verified in database",
            ),
            TaskPlanItem(
                task_key="task_3",
                description="Draft customized invitation email for student attendees",
                tool_name="draft_email",
                arguments={
                    "purpose": request,
                    "intended_audience": "Computer Science & Engineering Students",
                    "known_event_details": {
                        "topic": "Hands-on Workshop: Agentic AI Systems",
                        "date": "Next Saturday at 10:00 AM",
                        "venue": "Campus Main Auditorium",
                        "registration_deadline": "Friday 5:00 PM",
                    },
                    "tone": "enthusiastic and professional",
                },
                dependencies=["task_1"],
                expected_output="Invitation email draft with explicit missing field flags",
                completion_criteria="Email body structured without external dispatch",
            ),
        ],
    )


class CloudPlannerService:
    def __init__(self):
        self.settings = get_settings()

    def build_system_prompt(self) -> str:
        tools_list = default_tool_registry.list_tools()
        tools_desc = "\n".join(
            [f"- {t['name']}: {t['description']} | Schema: {json.dumps(t['input_schema'])}" for t in tools_list]
        )
        return (
            "You are the AI Planner for AutoPilot AI, an autonomous workflow engine.\n"
            "Your job is to convert natural language operational goals into a structured, validated DAG execution plan.\n\n"
            "MANDATORY RULES:\n"
            "1. ONLY propose tools from this registered list:\n"
            f"{tools_desc}\n\n"
            "2. DO NOT perform arithmetic yourself! Use 'calculate_budget' for any cost computations.\n"
            "3. Every task must have a unique 'task_key' (e.g. task_1, task_2).\n"
            "4. Specify prerequisites in 'dependencies' (e.g. ['task_1']). NEVER create circular dependencies.\n"
            "5. 'arguments' must conform STRICTLY to the tool's JSON schema.\n"
            "6. Output MUST BE strictly a valid JSON object matching this schema:\n"
            "{\n"
            '  "goal": "...",\n'
            '  "tasks": [\n'
            '    {"task_key": "task_1", "description": "...", "tool_name": "...", "arguments": {...}, "dependencies": []}\n'
            "  ]\n"
            "}"
        )

    async def plan(
        self,
        user_request: str,
        budget_limit: Optional[float] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowPlan:
        """
        Queries cloud-hosted GPT-OSS 120B to generate and validate a structured DAG plan.
        Falls back gracefully if API credentials are not configured or in offline test mode.
        """
        # If API key is not configured, use the deterministic fallback plan
        if not self.settings.LLM_API_KEY or self.settings.LLM_API_KEY.startswith("test-"):
            logger.info("Cloud LLM API key not configured; using deterministic fallback plan.")
            return generate_fallback_workshop_plan(user_request, budget_limit)

        system_prompt = self.build_system_prompt()
        user_prompt = f"Goal: {user_request}\n"
        if budget_limit is not None:
            user_prompt += f"Budget Limit: {budget_limit}\n"
        if extra_context:
            user_prompt += f"Additional Context: {json.dumps(extra_context)}\n"

        url = f"{self.settings.LLM_API_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.LLM_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.settings.LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        last_error = None
        for attempt in range(self.settings.MAX_PLANNER_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=self.settings.LLM_TIMEOUT_SECONDS) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code != 200:
                        raise CloudLLMError(
                            f"Cloud LLM API returned status {resp.status_code}: {resp.text}"
                        )
                    resp_json = resp.json()
                    content = resp_json["choices"][0]["message"]["content"]
                    parsed_json = json.loads(content)

                    # Strictly validate with Pydantic DAG schema
                    return WorkflowPlan.model_validate(parsed_json)

            except (httpx.TimeoutException, httpx.RequestError) as net_err:
                last_error = CloudLLMError(f"Cloud LLM connection error: {str(net_err)}")
            except (json.JSONDecodeError, KeyError, IndexError) as parse_err:
                last_error = PlanValidationError(f"Cloud LLM returned malformed JSON: {str(parse_err)}")
            except (ValidationError, ValueError) as val_err:
                last_error = PlanValidationError(f"Generated plan validation failed: {str(val_err)}")

            logger.warning(
                f"Planner attempt {attempt + 1}/{self.settings.MAX_PLANNER_RETRIES + 1} failed: {last_error}"
            )

        # If retries exhausted, raise or fallback
        if last_error:
            raise last_error
        raise CloudLLMError("Failed to obtain a valid plan from Cloud LLM")
