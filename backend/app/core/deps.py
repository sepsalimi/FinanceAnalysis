"""FastAPI dependencies for auth and household access."""

from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import MembershipRole
from app.models.household import HouseholdMembership
from app.models.user import UserAccount

WRITE_ROLES = {
    MembershipRole.OWNER.value,
    MembershipRole.ADMINISTRATOR.value,
    MembershipRole.MEMBER.value,
}


def get_token_from_request(
    authorization: str | None = Header(default=None),
    cookie_token: str | None = Cookie(default=None, alias="finance_access_token"),
) -> str:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1]
    if cookie_token:
        return cookie_token
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_request),
) -> UserAccount:
    try:
        user_id = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    user = db.get(UserAccount, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    return user


def require_household_membership(
    household_id: UUID,
    db: Session,
    user: UserAccount,
    write: bool = False,
) -> HouseholdMembership:
    membership = db.scalar(
        select(HouseholdMembership).where(
            HouseholdMembership.household_id == household_id,
            HouseholdMembership.user_id == user.id,
        )
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a household member")
    if write and membership.permission_role not in WRITE_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Read-only membership")
    return membership
