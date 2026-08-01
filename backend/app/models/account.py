"""Financial institution and account models."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AccountType, InstitutionType


class FinancialInstitution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "financial_institutions"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country: Mapped[str | None] = mapped_column(String(2))
    institution_type: Mapped[str] = mapped_column(
        String(64), default=InstitutionType.BANK.value, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class FinancialAccount(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "financial_accounts"

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    institution_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("financial_institutions.id", ondelete="SET NULL")
    )
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_type: Mapped[str] = mapped_column(
        String(64), default=AccountType.CHEQUING.value, nullable=False
    )
    account_subtype: Mapped[str | None] = mapped_column(String(64))
    last_four_digits: Mapped[str | None] = mapped_column(String(4))
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    primary_owner_member_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("household_members.id", ondelete="SET NULL")
    )
    ownership_allocation: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=lambda: {"type": "household", "allocations": []}
    )
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(19, 4), default=Decimal("0"))
    current_reconciled_balance: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    include_in_net_worth: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    include_in_cash_flow: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
