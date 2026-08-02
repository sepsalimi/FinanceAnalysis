"""Splitwise expense and overlap assessment models."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import MatchStatus


class ExternalParticipant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "external_participants"

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_system: Mapped[str | None] = mapped_column(String(64))
    source_participant_id: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)


class SplitwiseExpense(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "splitwise_expenses"

    source_record_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("source_records.id", ondelete="CASCADE"), index=True
    )
    native_splitwise_expense_id: Mapped[str | None] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(String(500))
    expense_date: Mapped[date | None] = mapped_column(Date, index=True)
    total_estimated_amount: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    currency: Mapped[str | None] = mapped_column(String(3))
    group_name: Mapped[str | None] = mapped_column(String(200))
    splitwise_category: Mapped[str | None] = mapped_column(String(200))
    paid_by_participant: Mapped[str | None] = mapped_column(String(200))
    created_by_participant: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class SplitwiseParticipantAllocation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "splitwise_participant_allocations"

    splitwise_expense_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("splitwise_expenses.id", ondelete="CASCADE"), index=True
    )
    household_member_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    external_participant_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    amount_paid: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    amount_owed: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    net_share: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    source_data: Mapped[dict | None] = mapped_column(JSONB)


class SplitwiseOverlapAssessment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "splitwise_overlap_assessments"

    splitwise_expense_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("splitwise_expenses.id", ondelete="CASCADE"), index=True
    )
    candidate_financial_event_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("canonical_financial_events.id", ondelete="CASCADE")
    )
    candidate_source_record_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    relationship_type: Mapped[str | None] = mapped_column(String(64))
    match_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    date_evidence: Mapped[str | None] = mapped_column(String(32))
    description_evidence: Mapped[str | None] = mapped_column(String(32))
    amount_evidence: Mapped[str | None] = mapped_column(String(32))
    payer_evidence: Mapped[str | None] = mapped_column(String(32))
    participant_evidence: Mapped[str | None] = mapped_column(String(32))
    evidence_for_match: Mapped[list] = mapped_column(JSONB, default=list)
    evidence_against_match: Mapped[list] = mapped_column(JSONB, default=list)
    suggested_allocated_amount: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    status: Mapped[str] = mapped_column(String(32), default=MatchStatus.NEEDS_REVIEW.value)
    llm_provider: Mapped[str | None] = mapped_column(String(64))
    llm_model: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str | None] = mapped_column(String(64))
    reviewed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
