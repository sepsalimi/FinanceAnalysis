"""API v1 route aggregation matching the frontend contract."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user, require_household_membership
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.account import FinancialAccount, FinancialInstitution
from app.models.enums import OverallAssessmentStatus
from app.models.events import CanonicalFinancialEvent
from app.models.household import Household, HouseholdMember
from app.models.importing import ImportInterpretation, ImportSnapshot, RawSourceRow, UploadedFile
from app.models.planning import Asset, Debt, PlannedOneTimeItem, RecurringCashFlowItem
from app.models.taxonomy import CategorizationRule, Category
from app.models.user import UserAccount
from app.schemas.common import (
    AccountCreate,
    AccountOut,
    ConfirmImportRequest,
    HouseholdOut,
    InterpretationUpdate,
    LoginRequest,
    MemberCreate,
    MemberOut,
    MemberUpdate,
    OnboardingRequest,
    RegisterRequest,
    UserOut,
)
from app.services import analytics as analytics_service
from app.services.households import add_member, create_household_with_members, list_user_households
from app.services.import_pipeline import (
    confirm_and_normalize,
    import_summary,
    serialize_interpretation,
    update_interpretation,
    upload_and_interpret,
)

api_router = APIRouter()


def _active_household(db: Session, user: UserAccount) -> Household:
    households = list_user_households(db, user.id)
    if not households:
        raise HTTPException(status_code=400, detail="No household. Complete onboarding first.")
    return households[0]


@api_router.post("/auth/register", response_model=UserOut, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserAccount:
    existing = db.scalar(select(UserAccount).where(UserAccount.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = UserAccount(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        display_name=payload.display_name.strip(),
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@api_router.post("/auth/login", response_model=UserOut)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> UserAccount:
    user = db.scalar(select(UserAccount).where(UserAccount.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user.last_login_at = datetime.now(UTC)
    db.commit()
    token = create_access_token(user.id)
    settings = get_settings()
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
    )
    return user


@api_router.post("/auth/logout")
def logout(response: Response) -> dict[str, str]:
    settings = get_settings()
    response.delete_cookie(settings.cookie_name)
    return {"message": "logged out"}


@api_router.get("/auth/me", response_model=UserOut)
def me(user: UserAccount = Depends(get_current_user)) -> UserAccount:
    return user


@api_router.post("/onboarding", response_model=HouseholdOut, status_code=201)
def onboard(
    payload: OnboardingRequest,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> Household:
    people = [p.model_dump() for p in payload.people]
    try:
        household = create_household_with_members(
            db,
            user=user,
            name=payload.household_name,
            default_currency=payload.currency,
            timezone=payload.timezone,
            locale=payload.locale,
            people=people,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return household


@api_router.get("/households", response_model=list[HouseholdOut])
def households(
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> list[Household]:
    return list_user_households(db, user.id)


@api_router.get("/household-settings")
def household_settings(
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    members = db.scalars(
        select(HouseholdMember).where(HouseholdMember.household_id == household.id)
    ).all()
    return {
        "items": [
            {
                "id": str(household.id),
                "name": household.name,
                "default_currency": household.default_currency,
                "timezone": household.timezone,
                "locale": household.locale,
                "assessment_confidence_settings": household.assessment_confidence_settings,
                "analytics_default_settings": household.analytics_default_settings,
                "members": [
                    {
                        "id": str(m.id),
                        "display_name": m.display_name,
                        "profile_role": m.profile_role,
                        "is_active": m.is_active,
                    }
                    for m in members
                ],
            }
        ],
        "total": 1,
    }


@api_router.post("/households/{household_id}/members", response_model=MemberOut, status_code=201)
def create_member(
    household_id: UUID,
    payload: MemberCreate,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> HouseholdMember:
    require_household_membership(household_id, db, user, write=True)
    return add_member(db, household_id, payload.display_name)


@api_router.patch("/households/{household_id}/members/{member_id}", response_model=MemberOut)
def patch_member(
    household_id: UUID,
    member_id: UUID,
    payload: MemberUpdate,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> HouseholdMember:
    require_household_membership(household_id, db, user, write=True)
    member = db.get(HouseholdMember, member_id)
    if not member or member.household_id != household_id:
        raise HTTPException(status_code=404, detail="Member not found")
    if payload.display_name is not None:
        member.display_name = payload.display_name.strip()
    if payload.is_active is not None:
        member.is_active = payload.is_active
    db.commit()
    db.refresh(member)
    return member


@api_router.get("/accounts")
def list_accounts(
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    accounts = db.scalars(
        select(FinancialAccount).where(FinancialAccount.household_id == household.id)
    ).all()
    items = [
        {
            "id": str(a.id),
            "account_name": a.account_name,
            "account_type": a.account_type,
            "currency": a.currency,
            "last_four_digits": a.last_four_digits,
            "opening_balance": str(a.opening_balance),
            "current_reconciled_balance": str(a.current_reconciled_balance)
            if a.current_reconciled_balance is not None
            else None,
            "is_active": a.is_active,
            "include_in_net_worth": a.include_in_net_worth,
            "include_in_cash_flow": a.include_in_cash_flow,
        }
        for a in accounts
    ]
    return {"items": items, "total": len(items)}


@api_router.post("/accounts", response_model=AccountOut, status_code=201)
def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> FinancialAccount:
    household = _active_household(db, user)
    require_household_membership(household.id, db, user, write=True)
    institution_id = None
    if payload.institution_name:
        inst = FinancialInstitution(name=payload.institution_name, institution_type="bank")
        db.add(inst)
        db.flush()
        institution_id = inst.id
    account = FinancialAccount(
        household_id=household.id,
        institution_id=institution_id,
        account_name=payload.account_name,
        account_type=payload.account_type,
        currency=(payload.currency or household.default_currency).upper(),
        last_four_digits=payload.last_four_digits,
        primary_owner_member_id=payload.primary_owner_member_id,
        opening_balance=Decimal(payload.opening_balance),
        current_reconciled_balance=Decimal(payload.opening_balance),
        include_in_net_worth=payload.include_in_net_worth,
        include_in_cash_flow=payload.include_in_cash_flow,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@api_router.get("/categories")
def list_categories(
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    cats = db.scalars(
        select(Category).where(
            (Category.household_id.is_(None)) | (Category.household_id == household.id),
            Category.is_active.is_(True),
        )
    ).all()
    items = [
        {
            "id": str(c.id),
            "name": c.name,
            "parent_category_id": str(c.parent_category_id) if c.parent_category_id else None,
            "category_level": c.category_level,
            "is_system_seeded": c.is_system_seeded,
        }
        for c in cats
    ]
    return {"items": items, "total": len(items)}


@api_router.get("/rules")
def list_rules(
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    rules = db.scalars(
        select(CategorizationRule).where(CategorizationRule.household_id == household.id)
    ).all()
    items = [
        {
            "id": str(r.id),
            "name": r.name,
            "match_type": r.match_type,
            "priority": r.priority,
            "is_active": r.is_active,
        }
        for r in rules
    ]
    return {"items": items, "total": len(items)}


@api_router.post("/imports/upload")
async def upload_import(
    file: UploadFile = File(...),
    source_name: str | None = Form(default=None),
    financial_account_id: UUID | None = Form(default=None),
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    require_household_membership(household.id, db, user, write=True)
    settings = get_settings()
    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=400, detail="File too large")
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    hint = None
    if source_name and "splitwise" in source_name.lower():
        hint = "splitwise"
    elif source_name and "credit" in source_name.lower():
        hint = "credit_card_statement"
    result = upload_and_interpret(
        db,
        household=household,
        user=user,
        filename=file.filename,
        data=data,
        financial_account_id=financial_account_id,
        source_type_hint=hint,
    )
    return {
        "id": result["import_snapshot_id"],
        "import_id": result["import_snapshot_id"],
        "uploaded_file_id": result["uploaded_file_id"],
        "identical_file_detected": result["identical_file_detected"],
        "interpretation": result["interpretation"],
    }


@api_router.get("/imports/interpretation")
def get_interpretation(
    import_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    snapshot = _get_snapshot(db, household.id, import_id)
    interpretation = db.scalar(
        select(ImportInterpretation).where(ImportInterpretation.import_snapshot_id == snapshot.id)
    )
    payload = serialize_interpretation(interpretation) or {}
    samples = payload.get("sample_normalized_rows") or []
    return {
        "items": samples,
        "total": len(samples),
        "interpretation": payload,
        "import_id": str(snapshot.id),
    }


@api_router.post("/imports/interpretation")
def post_interpretation(
    payload: InterpretationUpdate,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    snapshot_id = payload.import_id or payload.import_snapshot_id
    snapshot = _get_snapshot(db, household.id, snapshot_id)
    updates = payload.model_dump(exclude_none=True)
    corrections = updates.pop("corrections", None) or {}
    # Map frontend correction shorthand into interpretation fields
    if "column_mapping" in corrections and "column_mappings" not in updates:
        updates["column_mappings"] = [
            {
                "source_column": source,
                "normalized_field": field,
                "confidence": 1.0,
                "reason": "Human correction",
            }
            for source, field in corrections["column_mapping"].items()
        ]
    for key in (
        "source_type",
        "selected_worksheet",
        "header_row",
        "data_start_row",
        "data_end_row",
        "ignored_rows",
        "column_mappings",
        "date_format",
        "amount_convention",
        "default_currency",
        "description_template",
        "warnings",
    ):
        if key in corrections:
            updates[key] = corrections[key]
    updates.pop("import_id", None)
    updates.pop("import_snapshot_id", None)
    interpretation = update_interpretation(db, snapshot=snapshot, user=user, payload=updates)
    return {
        "items": interpretation.sample_normalized_rows or [],
        "total": len(interpretation.sample_normalized_rows or []),
        "interpretation": serialize_interpretation(interpretation),
        "import_id": str(snapshot.id),
    }


@api_router.get("/imports/confirm")
def get_confirm_preview(
    import_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    snapshot = _get_snapshot(db, household.id, import_id)
    summary = import_summary(db, snapshot)
    return {
        "items": [
            {
                "metric": "source_row_count",
                "value": summary["source_row_count"],
            },
            {"metric": "new_record_count", "value": summary["new_record_count"]},
            {"metric": "unchanged_record_count", "value": summary["unchanged_record_count"]},
            {"metric": "updated_record_count", "value": summary["updated_record_count"]},
            {"metric": "failed_row_count", "value": summary["failed_row_count"]},
            {"metric": "import_status", "value": summary["import_status"]},
        ],
        "total": 6,
        "summary": summary,
        "import_id": str(snapshot.id),
    }


@api_router.post("/imports/confirm")
def post_confirm(
    payload: ConfirmImportRequest,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    snapshot_id = payload.import_id or payload.import_snapshot_id
    snapshot = _get_snapshot(db, household.id, snapshot_id)
    summary = confirm_and_normalize(db, household=household, user=user, snapshot=snapshot)
    return {"items": [summary], "total": 1, "summary": summary, "import_id": str(snapshot.id)}


@api_router.get("/imports")
def list_imports(
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    snapshots = db.scalars(
        select(ImportSnapshot)
        .where(ImportSnapshot.household_id == household.id)
        .order_by(ImportSnapshot.created_at.desc())
    ).all()
    items = []
    for snap in snapshots:
        uploaded = db.get(UploadedFile, snap.uploaded_file_id)
        items.append(
            {
                "id": str(snap.id),
                "filename": uploaded.original_filename if uploaded else None,
                "source_type": snap.source_type,
                "import_status": snap.import_status,
                "source_row_count": snap.source_row_count,
                "new_record_count": snap.new_record_count,
                "unchanged_record_count": snap.unchanged_record_count,
                "updated_record_count": snap.updated_record_count,
                "failed_row_count": snap.failed_row_count,
            }
        )
    return {"items": items, "total": len(items)}


@api_router.get("/transactions")
def list_transactions(
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
    limit: int = Query(default=100, le=500),
) -> dict[str, Any]:
    household = _active_household(db, user)
    events = db.scalars(
        select(CanonicalFinancialEvent)
        .where(CanonicalFinancialEvent.household_id == household.id)
        .order_by(CanonicalFinancialEvent.event_date.desc().nullslast())
        .limit(limit)
    ).all()
    return {"items": [_event_row(db, e) for e in events], "total": len(events)}


@api_router.get("/review")
def review_queue(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    query = select(CanonicalFinancialEvent).where(
        CanonicalFinancialEvent.household_id == household.id
    )
    status_map = {
        "for_review": [
            OverallAssessmentStatus.NEEDS_REVIEW.value,
            OverallAssessmentStatus.PENDING_CATEGORY.value,
            OverallAssessmentStatus.PENDING_MATCH.value,
            OverallAssessmentStatus.UNASSESSED.value,
        ],
        "assessed": [
            OverallAssessmentStatus.ASSESSED.value,
            OverallAssessmentStatus.ASSESSED_WITH_WARNING.value,
        ],
        "pending_category": [OverallAssessmentStatus.PENDING_CATEGORY.value],
        "pending_match": [OverallAssessmentStatus.PENDING_MATCH.value],
        "possible_duplicates": None,
        "possible_transfers": None,
        "excluded": [OverallAssessmentStatus.EXCLUDED.value],
        "failed": [OverallAssessmentStatus.FAILED.value],
    }
    events = db.scalars(query.order_by(CanonicalFinancialEvent.event_date.desc().nullslast())).all()
    if status and status != "all":
        if status == "possible_duplicates":
            events = [e for e in events if e.duplicate_status == "possible"]
        elif status == "possible_transfers":
            events = [e for e in events if e.transfer_status in {"possible", "likely"}]
        elif status in status_map and status_map[status]:
            allowed = set(status_map[status] or [])
            events = [e for e in events if e.overall_assessment_status in allowed]

    all_events = db.scalars(
        select(CanonicalFinancialEvent).where(
            CanonicalFinancialEvent.household_id == household.id
        )
    ).all()
    assessed = sum(
        1
        for e in all_events
        if e.overall_assessment_status
        in {
            OverallAssessmentStatus.ASSESSED.value,
            OverallAssessmentStatus.ASSESSED_WITH_WARNING.value,
        }
    )
    return {
        "items": [_event_row(db, e) for e in events],
        "total": len(events),
        "stats": {
            "total_imported_rows": len(all_events),
            "fully_assessed_rows": assessed,
            "assessment_completion_pct": round((assessed / len(all_events) * 100), 1)
            if all_events
            else 100.0,
        },
    }


@api_router.get("/dashboard/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    return analytics_service.dashboard_summary(db, household)


@api_router.get("/cash-flow")
def cash_flow(
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    points = analytics_service.monthly_cash_flow(db, household.id)
    return {"items": points, "total": len(points)}


@api_router.get("/analytics")
def analytics(
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
    include_pending: bool = False,
) -> dict[str, Any]:
    household = _active_household(db, user)
    start = date.today().replace(day=1)
    items = analytics_service.category_spend(
        db, household.id, start=start, end=date.today(), include_pending=include_pending
    )
    return {"items": items, "total": len(items)}


@api_router.get("/one-time-items")
def one_time_items(
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    rows = db.scalars(
        select(PlannedOneTimeItem).where(PlannedOneTimeItem.household_id == household.id)
    ).all()
    items = [
        {
            "id": str(r.id),
            "description": r.description,
            "item_type": r.item_type,
            "expected_amount": str(r.expected_amount),
            "expected_date": r.expected_date.isoformat() if r.expected_date else None,
            "status": r.status,
        }
        for r in rows
    ]
    return {"items": items, "total": len(items)}


@api_router.get("/assets-and-debts")
def assets_and_debts(
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    assets = db.scalars(select(Asset).where(Asset.household_id == household.id)).all()
    debts = db.scalars(select(Debt).where(Debt.household_id == household.id)).all()
    items = [
        {
            "id": str(a.id),
            "kind": "asset",
            "description": a.description,
            "value": str(a.current_value),
            "currency": a.currency,
        }
        for a in assets
    ] + [
        {
            "id": str(d.id),
            "kind": "debt",
            "description": d.description,
            "value": str(d.current_balance),
            "currency": household.default_currency,
        }
        for d in debts
    ]
    return {"items": items, "total": len(items)}


@api_router.get("/data-quality")
def data_quality(
    db: Session = Depends(get_db),
    user: UserAccount = Depends(get_current_user),
) -> dict[str, Any]:
    household = _active_household(db, user)
    events = db.scalars(
        select(CanonicalFinancialEvent).where(
            CanonicalFinancialEvent.household_id == household.id
        )
    ).all()
    raw_count = db.scalar(
        select(RawSourceRow.id)
        .join(ImportSnapshot, ImportSnapshot.id == RawSourceRow.import_snapshot_id)
        .where(ImportSnapshot.household_id == household.id)
        .limit(1)
    )
    assessed = sum(
        1
        for e in events
        if e.overall_assessment_status
        in {
            OverallAssessmentStatus.ASSESSED.value,
            OverallAssessmentStatus.ASSESSED_WITH_WARNING.value,
        }
    )
    pending = sum(
        1
        for e in events
        if e.overall_assessment_status
        in {
            OverallAssessmentStatus.PENDING_CATEGORY.value,
            OverallAssessmentStatus.NEEDS_REVIEW.value,
            OverallAssessmentStatus.UNASSESSED.value,
        }
    )
    items = [
        {"metric": "canonical_events", "value": len(events)},
        {"metric": "assessed_events", "value": assessed},
        {"metric": "pending_events", "value": pending},
        {"metric": "has_raw_rows", "value": bool(raw_count)},
    ]
    return {"items": items, "total": len(items)}


def _get_snapshot(db: Session, household_id: UUID, import_id: UUID | None) -> ImportSnapshot:
    if import_id:
        snapshot = db.get(ImportSnapshot, import_id)
        if not snapshot or snapshot.household_id != household_id:
            raise HTTPException(status_code=404, detail="Import not found")
        return snapshot
    snapshot = db.scalar(
        select(ImportSnapshot)
        .where(ImportSnapshot.household_id == household_id)
        .order_by(ImportSnapshot.created_at.desc())
    )
    if not snapshot:
        raise HTTPException(status_code=404, detail="No imports found")
    return snapshot


def _event_row(db: Session, event: CanonicalFinancialEvent) -> dict[str, Any]:
    category = db.get(Category, event.confirmed_category_id) if event.confirmed_category_id else None
    subcategory = (
        db.get(Category, event.confirmed_subcategory_id) if event.confirmed_subcategory_id else None
    )
    account = (
        db.get(FinancialAccount, event.financial_account_id) if event.financial_account_id else None
    )
    return {
        "id": str(event.id),
        "date": event.event_date.isoformat() if event.event_date else None,
        "original_description": event.original_description,
        "normalized_merchant": event.confirmed_description,
        "account": account.account_name if account else None,
        "amount": str(event.confirmed_amount) if event.confirmed_amount is not None else None,
        "category": subcategory.name if subcategory else (category.name if category else None),
        "household_allocation": event.ownership_allocation,
        "transaction_type": event.event_type,
        "splitwise_match_status": event.splitwise_match_status,
        "llm_confidence": str(event.llm_confidence) if event.llm_confidence is not None else None,
        "overall_status": event.overall_assessment_status,
        "review_reason": event.review_reason,
        "analytics_inclusion_status": event.analytics_inclusion_status,
    }
