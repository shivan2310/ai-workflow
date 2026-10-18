from typing import List, Dict, Any
from pydantic import BaseModel, Field, model_validator, ValidationError
from app.tools.registry import default_tool_registry


class TaskPlanItem(BaseModel):
    task_key: str = Field(min_length=1, max_length=50, description="Unique identifier for the task (e.g. task_1)")
    description: str = Field(min_length=3, max_length=500, description="What this task accomplishes")
    tool_name: str = Field(min_length=1, max_length=100, description="Allowlisted registered tool name")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments tailored for the tool schema")
    dependencies: List[str] = Field(default_factory=list, description="List of prerequisite task_keys")
    expected_output: str = Field(default="", description="Expected result description")
    completion_criteria: str = Field(default="", description="How to determine task success")


class WorkflowPlan(BaseModel):
    goal: str = Field(min_length=5, max_length=1000, description="Overall workflow goal")
    tasks: List[TaskPlanItem] = Field(min_length=1, description="List of discrete tasks in the plan")

    @model_validator(mode="after")
    def validate_plan_dag_and_tools(self) -> "WorkflowPlan":
        task_keys = set()
        dep_graph: Dict[str, List[str]] = {}

        # 1. Unique task keys & tool registry verification
        for task in self.tasks:
            if task.task_key in task_keys:
                raise ValueError(f"Duplicate task_key found in plan: '{task.task_key}'")
            task_keys.add(task.task_key)
            dep_graph[task.task_key] = task.dependencies

            # Tool registry check
            tool_def = default_tool_registry.get(task.tool_name)
            if not tool_def:
                raise ValueError(
                    f"Unknown tool name '{task.tool_name}' in task '{task.task_key}'. "
                    f"Available tools: {[t['name'] for t in default_tool_registry.list_tools()]}"
                )

            # Argument validation against tool's Pydantic input schema
            try:
                tool_def.input_schema.model_validate(task.arguments)
            except ValidationError as err:
                raise ValueError(
                    f"Arguments for task '{task.task_key}' do not match tool '{task.tool_name}' schema: {err.errors()}"
                )

        # 2. Dependency existence check
        for task_key, deps in dep_graph.items():
            for dep in deps:
                if dep not in task_keys:
                    raise ValueError(
                        f"Task '{task_key}' declares dependency on non-existent task '{dep}'"
                    )
                if dep == task_key:
                    raise ValueError(
                        f"Task '{task_key}' cannot depend on itself"
                    )

        # 3. Cycle detection using Kahn's algorithm
        in_degree = {k: 0 for k in task_keys}
        for task_key, deps in dep_graph.items():
            in_degree[task_key] = len(deps)

        queue = [k for k, deg in in_degree.items() if deg == 0]
        visited_count = 0

        # Adjacency: who depends on this task
        dependents: Dict[str, List[str]] = {k: [] for k in task_keys}
        for task_key, deps in dep_graph.items():
            for dep in deps:
                dependents[dep].append(task_key)

        while queue:
            node = queue.pop(0)
            visited_count += 1
            for dependent in dependents[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if visited_count != len(task_keys):
            raise ValueError("Circular dependency detected in plan tasks (DAG cycle)")

        return self
