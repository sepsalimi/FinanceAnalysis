"""Shared Pydantic schemas."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int


class Message(BaseModel):
    message: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORMModel):
    id: UUID
    email: EmailStr
    display_name: str
    is_active: bool
    is_verified: bool


class PersonIn(BaseModel):
    name: str = ""
    email: str | None = None


class OnboardingRequest(BaseModel):
    household_name: str = Field(min_length=1, max_length=200)
    currency: str = Field(min_length=3, max_length=3)
    timezone: str = Field(min_length=1, max_length=100)
    locale: str | None = None
    people: list[PersonIn]


class HouseholdOut(ORMModel):
    id: UUID
    name: str
    default_currency: str
    timezone: str
    locale: str | None
    is_active: bool


class MemberOut(ORMModel):
    id: UUID
    display_name: str
    profile_role: str
    is_active: bool


class MemberCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=200)


class MemberUpdate(BaseModel):
    display_name: str | None = None
    is_active: bool | None = None


class AccountCreate(BaseModel):
    account_name: str
    account_type: str
    currency: str | None = None
    institution_name: str | None = None
    last_four_digits: str | None = None
    opening_balance: str = "0"
    primary_owner_member_id: UUID | None = None
    include_in_net_worth: bool = True
    include_in_cash_flow: bool = True


class AccountOut(ORMModel):
    id: UUID
    account_name: str
    account_type: str
    currency: str
    last_four_digits: str | None
    opening_balance: Any
    current_reconciled_balance: Any
    is_active: bool
    include_in_net_worth: bool
    include_in_cash_flow: bool


class InterpretationUpdate(BaseModel):
    import_id: UUID | None = None
    import_snapshot_id: UUID | None = None
    corrections: dict[str, Any] | None = None
    source_type: str | None = None
    selected_worksheet: str | None = None
    header_row: int | None = None
    data_start_row: int | None = None
    data_end_row: int | None = None
    ignored_rows: list[int] | None = None
    column_mappings: list[dict[str, Any]] | None = None
    date_format: str | None = None
    amount_convention: str | None = None
    default_currency: str | None = None
    description_template: str | None = None
    warnings: list[str] | None = None


class ConfirmImportRequest(BaseModel):
    import_id: UUID | None = None
    import_snapshot_id: UUID | None = None
