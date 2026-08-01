"""Dashboard and analytics queries over confirmed PostgreSQL records."""

from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import FinancialAccount
from app.models.enums import (
    AccountType,
    AnalyticsInclusionStatus,
    EventType,
    OverallAssessmentStatus,
)
from app.models.events import CanonicalFinancialEvent
from app.models.household import Household
from app.models.planning import Asset, Debt
from app.services.calculations import (
    assessment_completion_pct,
    net_cash_flow,
    savings_rate,
    sum_decimals,
)

ZERO = Decimal("0")
LIABILITY_TYPES = {
    AccountType.CREDIT_CARD.value,
    AccountType.LINE_OF_CREDIT.value,
    AccountType.LOAN.value,
    AccountType.MORTGAGE.value,
}


def _month_bounds(day: date | None = None) -> tuple[date, date]:
    day = day or date.today()
    start = day.replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = start.replace(month=start.month + 1, day=1) - timedelta(days=1)
    return start, end


def dashboard_summary(db: Session, household: Household) -> dict:
    start, end = _month_bounds()
    events = db.scalars(
        select(CanonicalFinancialEvent).where(
            CanonicalFinancialEvent.household_id == household.id,
            CanonicalFinancialEvent.event_date >= start,
            CanonicalFinancialEvent.event_date <= end,
        )
    ).all()

    confirmed_income = ZERO
    confirmed_expense = ZERO
    pending_expense = ZERO
    pending_count = 0
    assessed = 0
    for event in events:
        if event.overall_assessment_status == OverallAssessmentStatus.ASSESSED.value:
            assessed += 1
        amount = event.confirmed_amount or ZERO
        is_confirmed = (
            event.analytics_inclusion_status == AnalyticsInclusionStatus.INCLUDED.value
            and event.overall_assessment_status
            in {
                OverallAssessmentStatus.ASSESSED.value,
                OverallAssessmentStatus.ASSESSED_WITH_WARNING.value,
            }
        )
        is_pending = event.analytics_inclusion_status == AnalyticsInclusionStatus.PENDING.value
        if event.event_type == EventType.TRANSFER.value:
            continue
        if event.event_type == EventType.INCOME.value:
            if is_confirmed:
                confirmed_income += amount
        elif amount < 0 or event.event_type == EventType.EXPENSE.value:
            if is_confirmed:
                confirmed_expense += amount
            elif is_pending:
                pending_expense += amount
                pending_count += 1

    net = net_cash_flow(confirmed_income, confirmed_expense)
    rate = savings_rate(confirmed_income, net)

    accounts = db.scalars(
        select(FinancialAccount).where(
            FinancialAccount.household_id == household.id,
            FinancialAccount.is_active.is_(True),
            FinancialAccount.include_in_net_worth.is_(True),
        )
    ).all()
    assets = db.scalars(
        select(Asset).where(Asset.household_id == household.id, Asset.include_in_net_worth.is_(True))
    ).all()
    debts = db.scalars(
        select(Debt).where(Debt.household_id == household.id, Debt.is_active.is_(True))
    ).all()

    cash_balance = ZERO
    liability_accounts = ZERO
    for account in accounts:
        balance = account.current_reconciled_balance
        if balance is None:
            balance = account.opening_balance or ZERO
        if account.account_type in LIABILITY_TYPES:
            liability_accounts += abs(balance)
        else:
            cash_balance += balance

    asset_total = sum_decimals(a.current_value for a in assets)
    debt_total = sum_decimals(d.current_balance for d in debts) + liability_accounts
    net_worth = cash_balance + asset_total - debt_total

    review_count = db.scalar(
        select(func.count()).select_from(CanonicalFinancialEvent).where(
            CanonicalFinancialEvent.household_id == household.id,
            CanonicalFinancialEvent.overall_assessment_status.in_(
                [
                    OverallAssessmentStatus.NEEDS_REVIEW.value,
                    OverallAssessmentStatus.PENDING_CATEGORY.value,
                    OverallAssessmentStatus.PENDING_MATCH.value,
                    OverallAssessmentStatus.UNASSESSED.value,
                ]
            ),
        )
    ) or 0

    return {
        "household_name": household.name,
        "currency": household.default_currency,
        "timezone": household.timezone,
        "net_worth": str(net_worth),
        "cash_balance": str(cash_balance),
        "monthly_income": str(confirmed_income),
        "monthly_expenses": str(abs(confirmed_expense)),
        "pending_expenses": str(abs(pending_expense)),
        "pending_count": pending_count,
        "net_cash_flow": str(net),
        "savings_rate": str(rate) if rate is not None else None,
        "total_debt": str(debt_total),
        "pending_review_count": review_count,
        "assessment_completion_pct": str(assessment_completion_pct(assessed, len(events))),
        "confirmed_included_only": True,
    }


def monthly_cash_flow(db: Session, household_id: UUID, months: int = 6) -> list[dict]:
    today = date.today()
    start = (today.replace(day=1) - timedelta(days=months * 31)).replace(day=1)
    events = db.scalars(
        select(CanonicalFinancialEvent).where(
            CanonicalFinancialEvent.household_id == household_id,
            CanonicalFinancialEvent.event_date >= start,
            CanonicalFinancialEvent.analytics_inclusion_status
            == AnalyticsInclusionStatus.INCLUDED.value,
            CanonicalFinancialEvent.event_type != EventType.TRANSFER.value,
        )
    ).all()
    buckets: dict[str, dict[str, Decimal]] = {}
    for event in events:
        if not event.event_date or event.confirmed_amount is None:
            continue
        key = event.event_date.strftime("%Y-%m")
        bucket = buckets.setdefault(key, {"income": ZERO, "expenses": ZERO})
        if event.event_type == EventType.INCOME.value or event.confirmed_amount > 0:
            if event.event_type == EventType.INCOME.value:
                bucket["income"] += event.confirmed_amount
        if event.event_type == EventType.EXPENSE.value or event.confirmed_amount < 0:
            if event.event_type != EventType.INCOME.value:
                bucket["expenses"] += abs(event.confirmed_amount)
    points = []
    for period in sorted(buckets.keys()):
        income = buckets[period]["income"]
        expenses = buckets[period]["expenses"]
        points.append(
            {
                "period": period,
                "income": str(income),
                "expenses": str(expenses),
                "net": str(income - expenses),
            }
        )
    return points


def category_spend(
    db: Session,
    household_id: UUID,
    *,
    start: date,
    end: date,
    include_pending: bool = False,
) -> list[dict]:
    events = db.scalars(
        select(CanonicalFinancialEvent).where(
            CanonicalFinancialEvent.household_id == household_id,
            CanonicalFinancialEvent.event_date >= start,
            CanonicalFinancialEvent.event_date <= end,
            CanonicalFinancialEvent.event_type == EventType.EXPENSE.value,
        )
    ).all()
    from app.models.taxonomy import Category

    categories = {
        c.id: c
        for c in db.scalars(select(Category)).all()
    }
    totals: dict[str, dict] = {}
    for event in events:
        cat = categories.get(event.confirmed_category_id) if event.confirmed_category_id else None
        name = cat.name if cat else "Uncategorized"
        bucket = totals.setdefault(
            name,
            {
                "category": name,
                "confirmed_total": ZERO,
                "pending_total": ZERO,
                "pending_count": 0,
                "event_ids": [],
            },
        )
        amount = abs(event.confirmed_amount or ZERO)
        if event.analytics_inclusion_status == AnalyticsInclusionStatus.INCLUDED.value:
            bucket["confirmed_total"] += amount
            bucket["event_ids"].append(str(event.id))
        elif include_pending or event.analytics_inclusion_status == AnalyticsInclusionStatus.PENDING.value:
            bucket["pending_total"] += amount
            bucket["pending_count"] += 1
            bucket["event_ids"].append(str(event.id))
    return [
        {
            "category": v["category"],
            "confirmed_total": str(v["confirmed_total"]),
            "pending_total": str(v["pending_total"]),
            "pending_count": v["pending_count"],
            "pending_included": include_pending,
            "event_ids": v["event_ids"],
        }
        for v in sorted(totals.values(), key=lambda x: x["confirmed_total"], reverse=True)
    ]
