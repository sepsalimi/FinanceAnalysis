"""Canonical financial events, relationships, allocations, and splits."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    AnalyticsInclusionStatus,
    EventType,
    MatchStatus,
    OverallAssessmentStatus,
    RelationshipType,
)


class CanonicalFinancialEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "canonical_financial_events"

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    event_date: Mapped[date | None] = mapped_column(Date, index=True)
    posted_date: Mapped[date | None] = mapped_column(Date)
    event_type: Mapped[str] = mapped_column(
        String(64), default=EventType.UNKNOWN.value, index=True
    )
    confirmed_merchant_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    confirmed_description: Mapped[str | None] = mapped_column(String(500))
    original_description: Mapped[str | None] = mapped_column(String(1000))
    confirmed_amount: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    confirmed_currency: Mapped[str | None] = mapped_column(String(3))
    original_currency: Mapped[str | None] = mapped_column(String(3))
    original_amount: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    exchange_rate: Mapped[Decimal | None] = mapped_column(Numeric(19, 8))
    confirmed_category_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    confirmed_subcategory_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    household_economic_share: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    transaction_direction: Mapped[str | None] = mapped_column(String(16))
    recurring_status: Mapped[bool | None] = mapped_column(Boolean)
    fixed_or_variable_status: Mapped[str | None] = mapped_column(String(32))
    essential_or_discretionary_status: Mapped[str | None] = mapped_column(String(32))
    one_time_status: Mapped[bool | None] = mapped_column(Boolean)
    transfer_status: Mapped[str] = mapped_column(String(32), default="unknown")
    refund_status: Mapped[str] = mapped_column(String(32), default="unknown")
    reimbursement_status: Mapped[str] = mapped_column(String(32), default="unknown")
    duplicate_status: Mapped[str] = mapped_column(String(32), default="unknown")
    splitwise_match_status: Mapped[str] = mapped_column(String(32), default="not_applicable")
    analytics_inclusion_status: Mapped[str] = mapped_column(
        String(32), default=AnalyticsInclusionStatus.PENDING.value, index=True
    )
    overall_assessment_status: Mapped[str] = mapped_column(
        String(64), default=OverallAssessmentStatus.UNASSESSED.value, index=True
    )
    financial_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("financial_accounts.id", ondelete="SET NULL"), index=True
    )
    ownership_allocation: Mapped[dict] = mapped_column(
        JSONB, default=lambda: {"type": "household", "allocations": []}
    )
    llm_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    review_reason: Mapped[str | None] = mapped_column(Text)
    user_notes: Mapped[str | None] = mapped_column(Text)
    is_category_user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_allocation_user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)


class SourceEventRelationship(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "source_event_relationships"

    source_record_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("source_records.id", ondelete="CASCADE"), index=True
    )
    canonical_financial_event_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("canonical_financial_events.id", ondelete="CASCADE"),
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(64), default=RelationshipType.PRIMARY_PAYMENT_EVIDENCE.value
    )
    allocated_amount: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    match_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    match_method: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default=MatchStatus.SUGGESTED.value)
    evidence: Mapped[dict | None] = mapped_column(JSONB)
    confirmed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FinancialEventAllocation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "financial_event_allocations"

    canonical_financial_event_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("canonical_financial_events.id", ondelete="CASCADE"),
        index=True,
    )
    household_member_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("household_members.id", ondelete="SET NULL")
    )
    external_participant_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    allocation_type: Mapped[str] = mapped_column(String(64), default="share")
    allocation_percentage: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    allocation_amount: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    paid_amount: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    owed_amount: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    net_amount: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)


class TransactionSplit(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "transaction_splits"

    canonical_financial_event_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("canonical_financial_events.id", ondelete="CASCADE"),
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    category_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    subcategory_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    household_member_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    notes: Mapped[str | None] = mapped_column(Text)
