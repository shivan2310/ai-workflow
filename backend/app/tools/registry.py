import inspect
from typing import Dict, Any, Callable, Type, Optional, List
from pydantic import BaseModel, ValidationError
from app.core.exceptions import ToolExecutionError, PlanValidationError
from app.schemas.tools import (
    CalculateBudgetInput,
    CalculateBudgetOutput,
    CreateTasksInput,
    CreateTasksOutput,
    DraftEmailInput,
    DraftEmailOutput,
)
from app.tools.budget import calculate_budget
from app.tools.tasks import create_tasks
from app.tools.email_drafter import draft_email


class ToolDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Type[BaseModel],
        output_schema: Type[BaseModel],
        func: Callable,
        requires_approval: bool = False,
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.func = func
        self.requires_approval = requires_approval


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool_def: ToolDefinition):
        self._tools[tool_def.name] = tool_def

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def is_registered(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema.model_json_schema(),
                "requires_approval": t.requires_approval,
            }
            for t in self._tools.values()
        ]

    def execute(
        self,
        name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> BaseModel:
        tool_def = self.get(name)
        if not tool_def:
            raise ToolExecutionError(f"Attempted execution of unregistered tool: '{name}'")

        # Validate input arguments against Pydantic input schema
        try:
            validated_input = tool_def.input_schema.model_validate(arguments)
        except ValidationError as err:
            raise PlanValidationError(
                f"Invalid arguments for tool '{name}': {err.errors()}",
                detail=err.errors(),
            )

        # Call tool with context if accepted
        try:
            sig = inspect.signature(tool_def.func)
            if "context" in sig.parameters:
                raw_output = tool_def.func(validated_input, context=context)
            else:
                raw_output = tool_def.func(validated_input)

            # Validate output against output schema
            if isinstance(raw_output, tool_def.output_schema):
                return raw_output
            return tool_def.output_schema.model_validate(raw_output)
        except (ToolExecutionError, PlanValidationError):
            raise
        except Exception as err:
            raise ToolExecutionError(f"Execution of tool '{name}' failed: {str(err)}")


# Global Tool Registry instance with default registered tools
default_tool_registry = ToolRegistry()

default_tool_registry.register(
    ToolDefinition(
        name="calculate_budget",
        description="Calculates workshop budget item totals, checks limit ceiling, and flags overruns.",
        input_schema=CalculateBudgetInput,
        output_schema=CalculateBudgetOutput,
        func=calculate_budget,
        requires_approval=False,
    )
)

default_tool_registry.register(
    ToolDefinition(
        name="create_tasks",
        description="Persists preparatory tasks and deadlines into the database under user ownership.",
        input_schema=CreateTasksInput,
        output_schema=CreateTasksOutput,
        func=create_tasks,
        requires_approval=False,
    )
)

default_tool_registry.register(
    ToolDefinition(
        name="draft_email",
        description="Generates an invitation email draft preview without external side effects.",
        input_schema=DraftEmailInput,
        output_schema=DraftEmailOutput,
        func=draft_email,
        requires_approval=False,
    )
)
