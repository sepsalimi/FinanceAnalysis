"""Categories, merchants, rules, and categorization assessment models."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import CategoryProposalStatus


class Category(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "categories"

    household_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    parent_category_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system_seeded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Merchant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "merchants"

    household_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    canonical_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    website: Mapped[str | None] = mapped_column(String(500))
    default_category_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL")
    )
    default_subcategory_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class MerchantAlias(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "merchant_aliases"

    merchant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), index=True
    )
    alias: Mapped[str] = mapped_column(String(300), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(String(64))
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))


class CategoryProposal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "category_proposals"

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    proposed_name: Mapped[str] = mapped_column(String(200), nullable=False)
    proposed_parent_category_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    proposed_category_level: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    proposed_description: Mapped[str | None] = mapped_column(Text)
    reason_existing_insufficient: Mapped[str | None] = mapped_column(Text)
    example_event_ids: Mapped[list] = mapped_column(JSONB, default=list)
    affected_event_count: Mapped[int] = mapped_column(Integer, default=0)
    total_amount_affected: Mapped[Decimal] = mapped_column(Numeric(19, 4), default=Decimal("0"))
    llm_provider: Mapped[str | None] = mapped_column(String(64))
    llm_model: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str | None] = mapped_column(String(64))
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    status: Mapped[str] = mapped_column(
        String(64), default=CategoryProposalStatus.PENDING.value, nullable=False, index=True
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_category_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)


class CategorizationAssessment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "categorization_assessments"

    canonical_financial_event_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("canonical_financial_events.id", ondelete="CASCADE"),
        index=True,
    )
    source_record_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("source_records.id", ondelete="SET NULL")
    )
    suggested_transaction_type: Mapped[str | None] = mapped_column(String(64))
    suggested_merchant: Mapped[str | None] = mapped_column(String(300))
    suggested_category_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    suggested_subcategory_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    suggested_ownership_allocation: Mapped[dict | None] = mapped_column(JSONB)
    suggested_recurring_status: Mapped[bool | None] = mapped_column(Boolean)
    suggested_fixed_or_variable: Mapped[str | None] = mapped_column(String(32))
    suggested_essential_or_discretionary: Mapped[str | None] = mapped_column(String(32))
    transfer_likelihood: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    refund_likelihood: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    category_fit: Mapped[str | None] = mapped_column(String(64))
    decision_method: Mapped[str | None] = mapped_column(String(64))
    llm_provider: Mapped[str | None] = mapped_column(String(64))
    llm_model: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str | None] = mapped_column(String(64))
    structured_model_output: Mapped[dict | None] = mapped_column(JSONB)
    explanation: Mapped[str | None] = mapped_column(Text)
    needs_human_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    review_reason: Mapped[str | None] = mapped_column(Text)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user_override_details: Mapped[dict | None] = mapped_column(JSONB)


class CategorizationRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "categorization_rules"

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    match_type: Mapped[str] = mapped_column(String(64), nullable=False)
    match_configuration: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    category_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    subcategory_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    merchant_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    household_member_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_human_confirmed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
