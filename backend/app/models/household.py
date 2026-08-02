"""Household, member, and membership models."""

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import MemberProfileRole, MembershipRole


class Household(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "households"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    default_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False)
    locale: Mapped[str | None] = mapped_column(String(32))
    assessment_confidence_settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "auto_accept": 0.90,
            "review": 0.70,
            "splitwise_auto_link": 0.95,
            "splitwise_review": 0.75,
        },
    )
    analytics_default_settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {"include_pending": False},
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    members = relationship("HouseholdMember", back_populates="household")
    memberships = relationship("HouseholdMembership", back_populates="household")


class HouseholdMember(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "household_members"

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    user_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="SET NULL"), index=True
    )
    profile_role: Mapped[str] = mapped_column(
        String(64), default=MemberProfileRole.FINANCIAL_PARTICIPANT.value, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    household = relationship("Household", back_populates="members")


class HouseholdMembership(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "household_memberships"
    __table_args__ = (UniqueConstraint("user_id", "household_id", name="uq_membership_user_hh"),)

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="CASCADE"), index=True
    )
    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    household_member_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("household_members.id", ondelete="CASCADE"), index=True
    )
    permission_role: Mapped[str] = mapped_column(
        String(32), default=MembershipRole.OWNER.value, nullable=False
    )

    user = relationship("UserAccount", back_populates="memberships")
    household = relationship("Household", back_populates="memberships")
