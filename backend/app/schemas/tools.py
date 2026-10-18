from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class BudgetItem(BaseModel):
    name: str = Field(min_length=1, max_length=200, description="Expense item name")
    amount: Decimal = Field(ge=0, description="Cost amount in currency unit (must be non-negative)")

    @field_validator("amount")
    @classmethod
    def validate_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Amount cannot be negative")
        return v.quantize(Decimal("0.01"))


class CalculateBudgetInput(BaseModel):
    items: List[BudgetItem] = Field(min_length=1, description="List of budget expense items")
    budget_limit: Decimal = Field(ge=0, description="Maximum budget limit ceiling")

    @field_validator("budget_limit")
    @classmethod
    def validate_limit(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Budget limit cannot be negative")
        return v.quantize(Decimal("0.01"))


class CalculateBudgetOutput(BaseModel):
    items: List[BudgetItem]
    total_estimated_cost: Decimal
    budget_limit: Decimal
    remaining_amount: Decimal
    overrun_amount: Decimal
    is_within_budget: bool


class TaskItemInput(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    deadline_days: Optional[int] = Field(default=None, ge=1, le=365)


class CreateTasksInput(BaseModel):
    tasks: List[TaskItemInput] = Field(min_length=1, description="List of preparation tasks to persist")


class CreatedTaskDetail(BaseModel):
    id: str
    task_key: str
    description: str
    priority: str
    status: str


class CreateTasksOutput(BaseModel):
    created_tasks: List[CreatedTaskDetail]
    total_created: int


class DraftEmailInput(BaseModel):
    purpose: str = Field(min_length=3, max_length=500, description="Purpose of the email")
    intended_audience: str = Field(min_length=2, max_length=200, description="Target recipient audience")
    known_event_details: Dict[str, Any] = Field(default_factory=dict, description="Verified details of the event")
    tone: Optional[str] = Field(default="professional", max_length=50)


class DraftEmailOutput(BaseModel):
    subject: str
    body: str
    missing_information: List[str]
    is_draft_only: bool = True
