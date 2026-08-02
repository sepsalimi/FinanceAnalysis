"""Documented financial calculation helpers. Money uses Decimal only."""

from decimal import Decimal
from typing import Iterable

from app.models.enums import Frequency

ZERO = Decimal("0")

ANNUALIZATION_MULTIPLIERS: dict[str, Decimal] = {
    Frequency.WEEKLY.value: Decimal("52"),
    Frequency.BIWEEKLY.value: Decimal("26"),
    Frequency.SEMIMONTHLY.value: Decimal("24"),
    Frequency.MONTHLY.value: Decimal("12"),
    Frequency.EVERY_TWO_MONTHS.value: Decimal("6"),
    Frequency.QUARTERLY.value: Decimal("4"),
    Frequency.SEMIANNUALLY.value: Decimal("2"),
    Frequency.ANNUALLY.value: Decimal("1"),
}


def annualize(amount: Decimal, frequency: str, custom_interval_days: int | None = None) -> Decimal:
    if frequency == Frequency.CUSTOM_INTERVAL.value:
        if not custom_interval_days or custom_interval_days <= 0:
            raise ValueError("custom_interval_days must be positive for custom frequency")
        return amount * (Decimal("365") / Decimal(custom_interval_days))
    multiplier = ANNUALIZATION_MULTIPLIERS.get(frequency)
    if multiplier is None:
        raise ValueError(f"Unsupported frequency: {frequency}")
    return amount * multiplier


def savings_rate(income_total: Decimal, net_cash_flow: Decimal) -> Decimal | None:
    if income_total == ZERO:
        return None
    return net_cash_flow / income_total


def net_cash_flow(income_total: Decimal, expense_total_signed: Decimal) -> Decimal:
    """expense_total_signed should be negative for outflows."""
    return income_total + expense_total_signed


def sum_decimals(values: Iterable[Decimal | None]) -> Decimal:
    total = ZERO
    for value in values:
        if value is not None:
            total += value
    return total


def percent_change(current: Decimal, previous: Decimal) -> Decimal | None:
    if previous == ZERO:
        return None
    return (current - previous) / abs(previous)


def assessment_completion_pct(assessed: int, total: int) -> Decimal:
    if total <= 0:
        return Decimal("100")
    return (Decimal(assessed) / Decimal(total) * Decimal("100")).quantize(Decimal("0.1"))


def splits_sum_to_amount(split_amounts: Iterable[Decimal], event_amount: Decimal) -> bool:
    return sum_decimals(split_amounts) == event_amount


def amount_within_splitwise_tolerance(
    splitwise_amount: Decimal,
    candidate_amount: Decimal,
) -> bool:
    """Candidate-only tolerance. Never confirms a match alone."""
    abs_sw = abs(splitwise_amount)
    abs_cand = abs(candidate_amount)
    diff = abs(abs_sw - abs_cand)
    if abs_sw < Decimal("100"):
        return diff <= Decimal("10")
    if abs_sw <= Decimal("500"):
        return diff <= abs_sw * Decimal("0.20")
    return diff <= abs_sw * Decimal("0.15")
