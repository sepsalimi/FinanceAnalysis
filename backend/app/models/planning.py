"""Recurring items, planned items, assets, debts, and budgets."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import Frequency, PlannedItemStatus


class RecurringCashFlowItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "recurring_cash_flow_items"

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    responsible_member_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    ownership_allocation: Mapped[dict] = mapped_column(
        JSONB, default=lambda: {"type": "household", "allocations": []}
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(64), nullable=False)
    category_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    subcategory_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    frequency: Mapped[str] = mapped_column(String(64), default=Frequency.MONTHLY.value)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    next_expected_date: Mapped[date | None] = mapped_column(Date)
    annualized_amount: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    debt_remaining: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    linked_debt_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    linked_merchant_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    linked_account_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    is_variable_amount: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)


class PlannedOneTimeItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "planned_one_time_items"

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    responsible_member_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    ownership_allocation: Mapped[dict] = mapped_column(
        JSONB, default=lambda: {"type": "household", "allocations": []}
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    item_type: Mapped[str] = mapped_column(String(64), nullable=False)
    category_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    subcategory_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    expected_date: Mapped[date | None] = mapped_column(Date)
    expected_month: Mapped[str | None] = mapped_column(String(7))
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    actual_linked_event_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(64), default=PlannedItemStatus.PLANNED.value)
    notes: Mapped[str | None] = mapped_column(Text)


class Asset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assets"

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    owner_member_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    ownership_allocation: Mapped[dict] = mapped_column(
        JSONB, default=lambda: {"type": "household", "allocations": []}
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    institution_or_location: Mapped[str | None] = mapped_column(String(200))
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    current_value: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    value_date: Mapped[date | None] = mapped_column(Date)
    include_in_net_worth: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)


class AssetSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "asset_snapshots"

    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), index=True
    )
    value: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str | None] = mapped_column(String(64))


class Debt(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "debts"

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    responsible_member_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    ownership_allocation: Mapped[dict] = mapped_column(
        JSONB, default=lambda: {"type": "household", "allocations": []}
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    lender: Mapped[str | None] = mapped_column(String(200))
    original_principal: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    current_balance: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    minimum_payment: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    payment_frequency: Mapped[str | None] = mapped_column(String(64))
    start_date: Mapped[date | None] = mapped_column(Date)
    expected_payoff_date: Mapped[date | None] = mapped_column(Date)
    financial_account_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)


class DebtSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "debt_snapshots"

    debt_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("debts.id", ondelete="CASCADE"), index=True
    )
    balance: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str | None] = mapped_column(String(64))


class Budget(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "budgets"

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    subcategory_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    period_type: Mapped[str] = mapped_column(String(32), default="monthly")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    household_member_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    ownership_allocation: Mapped[dict] = mapped_column(
        JSONB, default=lambda: {"type": "household", "allocations": []}
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
