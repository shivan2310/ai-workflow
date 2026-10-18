from decimal import Decimal
from app.schemas.tools import CalculateBudgetInput, CalculateBudgetOutput


def calculate_budget(input_data: CalculateBudgetInput) -> CalculateBudgetOutput:
    """
    Deterministically computes line item sums and checks budget ceilings
    using Python Decimal arithmetic to prevent floating-point inaccuracies.
    """
    total = sum((item.amount for item in input_data.items), Decimal("0.00")).quantize(Decimal("0.01"))
    limit = input_data.budget_limit.quantize(Decimal("0.01"))

    if total <= limit:
        remaining = (limit - total).quantize(Decimal("0.01"))
        overrun = Decimal("0.00")
        is_within_budget = True
    else:
        remaining = Decimal("0.00")
        overrun = (total - limit).quantize(Decimal("0.01"))
        is_within_budget = False

    return CalculateBudgetOutput(
        items=input_data.items,
        total_estimated_cost=total,
        budget_limit=limit,
        remaining_amount=remaining,
        overrun_amount=overrun,
        is_within_budget=is_within_budget,
    )
