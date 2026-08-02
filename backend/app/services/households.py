"""Household onboarding and member management."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import MemberProfileRole, MembershipRole
from app.models.household import Household, HouseholdMember, HouseholdMembership
from app.models.user import UserAccount
from app.services.audit import record_audit


def create_household_with_members(
    db: Session,
    *,
    user: UserAccount,
    name: str,
    default_currency: str,
    timezone: str,
    locale: str | None,
    people: list[dict],
) -> Household:
    if not people or not people[0].get("name", "").strip():
        raise ValueError("Person 1 name is required")

    household = Household(
        name=name.strip(),
        default_currency=default_currency.strip().upper(),
        timezone=timezone.strip(),
        locale=locale,
        is_active=True,
    )
    db.add(household)
    db.flush()

    primary_member = None
    for index, person in enumerate(people):
        display_name = (person.get("name") or "").strip()
        if not display_name:
            continue
        member = HouseholdMember(
            household_id=household.id,
            display_name=display_name,
            user_account_id=user.id if index == 0 else None,
            profile_role=(
                MemberProfileRole.HOUSEHOLD_ADMINISTRATOR.value
                if index == 0
                else MemberProfileRole.FINANCIAL_PARTICIPANT.value
            ),
            is_active=True,
        )
        db.add(member)
        db.flush()
        if index == 0:
            primary_member = member

    assert primary_member is not None
    membership = HouseholdMembership(
        user_id=user.id,
        household_id=household.id,
        household_member_id=primary_member.id,
        permission_role=MembershipRole.OWNER.value,
    )
    db.add(membership)
    record_audit(
        db,
        household_id=household.id,
        user_id=user.id,
        action="household.created",
        entity_type="household",
        entity_id=household.id,
        new_value={
            "name": household.name,
            "default_currency": household.default_currency,
            "member_count": len([p for p in people if (p.get("name") or "").strip()]),
        },
    )
    db.commit()
    db.refresh(household)
    return household


def add_member(db: Session, household_id: UUID, display_name: str) -> HouseholdMember:
    member = HouseholdMember(
        household_id=household_id,
        display_name=display_name.strip(),
        profile_role=MemberProfileRole.FINANCIAL_PARTICIPANT.value,
        is_active=True,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def list_user_households(db: Session, user_id: UUID) -> list[Household]:
    return list(
        db.scalars(
            select(Household)
            .join(HouseholdMembership, HouseholdMembership.household_id == Household.id)
            .where(HouseholdMembership.user_id == user_id, Household.is_active.is_(True))
        ).all()
    )
