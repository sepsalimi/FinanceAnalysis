"""Two-stage import pipeline: interpretation then normalization/assessment."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.llm.base import FileInterpretationResult, get_llm_provider
from app.models.enums import (
    AnalyticsInclusionStatus,
    EventType,
    ImportStatus,
    JobStatus,
    JobType,
    OverallAssessmentStatus,
    RelationshipType,
    RowClassification,
    SourceRecordStatus,
    SourceType,
)
from app.models.events import CanonicalFinancialEvent, SourceEventRelationship
from app.models.household import Household
from app.models.importing import (
    ImportInterpretation,
    ImportJob,
    ImportSnapshot,
    RawSourceRow,
    SourceRecord,
    SourceRecordVersion,
    UploadedFile,
)
from app.models.taxonomy import CategorizationAssessment, Category, CategoryProposal
from app.models.user import UserAccount
from app.services.audit import record_audit
from app.services.extraction import (
    build_structural_summary,
    detect_file_type,
    extract_workbook,
    nonempty_row,
)
from app.services.fingerprints import (
    canonical_identity_fingerprint,
    content_fingerprint,
    normalize_description,
    row_fingerprint,
    stable_source_key,
)
from app.services.money import normalize_signed_amount, parse_date, parse_decimal
from app.services.status_engine import compute_overall_status
from app.storage.base import get_storage, sha256_bytes


def upload_and_interpret(
    db: Session,
    *,
    household: Household,
    user: UserAccount,
    filename: str,
    data: bytes,
    financial_account_id: UUID | None,
    source_type_hint: str | None = None,
) -> dict[str, Any]:
    file_hash = sha256_bytes(data)
    existing_file = db.scalar(
        select(UploadedFile).where(
            UploadedFile.household_id == household.id,
            UploadedFile.sha256_hash == file_hash,
            UploadedFile.deletion_status == "active",
        )
    )
    identical_prior = existing_file is not None

    storage = get_storage()
    storage_key = f"{household.id}/{file_hash}/{filename}"
    if not identical_prior or not storage.exists(storage_key):
        storage.put_bytes(storage_key, data, content_type="application/octet-stream")

    uploaded = UploadedFile(
        household_id=household.id,
        uploaded_by=user.id,
        original_filename=filename,
        file_type=detect_file_type(filename),
        storage_key=storage_key,
        sha256_hash=file_hash,
        file_size=len(data),
        uploaded_at=datetime.now(UTC),
        detected_source_type=source_type_hint or SourceType.UNKNOWN.value,
        import_status=ImportStatus.INTERPRETING.value,
    )
    db.add(uploaded)
    db.flush()

    snapshot = ImportSnapshot(
        household_id=household.id,
        uploaded_file_id=uploaded.id,
        source_type=source_type_hint or SourceType.UNKNOWN.value,
        financial_account_id=financial_account_id,
        import_status=ImportStatus.INTERPRETING.value,
        started_at=datetime.now(UTC),
    )
    db.add(snapshot)
    db.flush()

    job = ImportJob(
        import_snapshot_id=snapshot.id,
        job_type=JobType.INTERPRET.value,
        status=JobStatus.RUNNING.value,
        current_stage="extract_and_interpret",
        progress_percentage=Decimal("10"),
        started_at=datetime.now(UTC),
        idempotency_key=f"interpret:{file_hash}:{snapshot.id}",
    )
    db.add(job)
    db.flush()

    if identical_prior:
        # Still create a snapshot/job for auditability, but mark warning.
        job.warning_details = {
            "identical_file": True,
            "message": "Identical file content previously uploaded. Confirming import will not create duplicates.",
        }

    workbook = extract_workbook(filename, data)
    summary = build_structural_summary(
        workbook,
        default_currency=household.default_currency,
        guessed_source_type=source_type_hint or "bank_statement",
    )
    llm = get_llm_provider(household)
    interpretation_result = llm.interpret_file(summary)
    sample_rows = _preview_normalized_rows(workbook, interpretation_result, limit=5)

    interpretation = ImportInterpretation(
        import_snapshot_id=snapshot.id,
        source_type=interpretation_result.source_type,
        selected_worksheet=interpretation_result.selected_sheet,
        selected_table_range=None,
        header_row=interpretation_result.header_row,
        data_start_row=interpretation_result.data_start_row,
        data_end_row=interpretation_result.data_end_row,
        ignored_rows=interpretation_result.ignored_rows,
        column_mappings=[c.model_dump() for c in interpretation_result.columns],
        date_format=interpretation_result.date_format,
        amount_convention=interpretation_result.amount_convention,
        default_currency=interpretation_result.default_currency,
        description_template=interpretation_result.description_template,
        confidence=Decimal(str(interpretation_result.overall_confidence)),
        warnings=interpretation_result.warnings,
        sample_normalized_rows=sample_rows,
        structural_summary=summary,
        prompt_version="file_interpret_v1",
        llm_provider=llm.provider_name,
        llm_model=llm.model_name,
    )
    db.add(interpretation)

    uploaded.detected_source_type = interpretation_result.source_type
    uploaded.import_status = ImportStatus.AWAITING_CONFIRMATION.value
    snapshot.source_type = interpretation_result.source_type
    snapshot.import_status = ImportStatus.AWAITING_CONFIRMATION.value
    snapshot.source_row_count = int(summary.get("row_count_estimate") or 0)
    job.status = JobStatus.COMPLETED.value
    job.progress_percentage = Decimal("100")
    job.completed_at = datetime.now(UTC)
    job.current_stage = "awaiting_confirmation"

    record_audit(
        db,
        household_id=household.id,
        user_id=user.id,
        action="file.uploaded_interpreted",
        entity_type="import_snapshot",
        entity_id=snapshot.id,
        new_value={
            "filename": filename,
            "sha256": file_hash,
            "identical_prior": identical_prior,
            "confidence": str(interpretation.confidence),
        },
    )
    db.commit()
    db.refresh(interpretation)
    db.refresh(snapshot)
    return {
        "uploaded_file_id": str(uploaded.id),
        "import_snapshot_id": str(snapshot.id),
        "identical_file_detected": identical_prior,
        "interpretation": serialize_interpretation(interpretation),
    }


def update_interpretation(
    db: Session,
    *,
    snapshot: ImportSnapshot,
    user: UserAccount,
    payload: dict[str, Any],
) -> ImportInterpretation:
    interpretation = db.scalar(
        select(ImportInterpretation).where(ImportInterpretation.import_snapshot_id == snapshot.id)
    )
    if not interpretation:
        raise ValueError("Interpretation not found")
    if interpretation.is_human_confirmed:
        raise ValueError("Interpretation already confirmed")

    for field in (
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
        if field in payload and payload[field] is not None:
            setattr(interpretation, field, payload[field])

    # Refresh sample rows after correction
    storage = get_storage()
    uploaded = db.get(UploadedFile, snapshot.uploaded_file_id)
    assert uploaded is not None
    data = storage.get_bytes(uploaded.storage_key)
    workbook = extract_workbook(uploaded.original_filename, data)
    result = FileInterpretationResult(
        source_type=interpretation.source_type,  # type: ignore[arg-type]
        institution_or_source=None,
        selected_sheet=interpretation.selected_worksheet,
        header_row=interpretation.header_row or 0,
        data_start_row=interpretation.data_start_row or 1,
        data_end_row=interpretation.data_end_row,
        ignored_rows=interpretation.ignored_rows or [],
        columns=interpretation.column_mappings,  # validated below by pydantic in callers
        amount_convention=interpretation.amount_convention or "requires_review",  # type: ignore[arg-type]
        date_format=interpretation.date_format,
        default_currency=interpretation.default_currency or "USD",
        description_template=interpretation.description_template or "{description}",
        warnings=interpretation.warnings or [],
        overall_confidence=float(interpretation.confidence or 0),
    )
    # column_mappings may be dicts; rebuild via model
    result = FileInterpretationResult.model_validate(
        {
            **result.model_dump(),
            "columns": interpretation.column_mappings,
        }
    )
    interpretation.sample_normalized_rows = _preview_normalized_rows(workbook, result, limit=5)
    record_audit(
        db,
        household_id=snapshot.household_id,
        user_id=user.id,
        action="import.interpretation_updated",
        entity_type="import_interpretation",
        entity_id=interpretation.id,
        new_value=payload,
    )
    db.commit()
    db.refresh(interpretation)
    return interpretation


def confirm_and_normalize(
    db: Session,
    *,
    household: Household,
    user: UserAccount,
    snapshot: ImportSnapshot,
) -> dict[str, Any]:
    interpretation = db.scalar(
        select(ImportInterpretation).where(ImportInterpretation.import_snapshot_id == snapshot.id)
    )
    if not interpretation:
        raise ValueError("Interpretation not found")
    if interpretation.is_human_confirmed and snapshot.import_status == ImportStatus.COMPLETED.value:
        return import_summary(db, snapshot)

    interpretation.is_human_confirmed = True
    interpretation.confirmed_by = user.id
    interpretation.confirmed_at = datetime.now(UTC)
    snapshot.import_status = ImportStatus.PROCESSING.value
    uploaded = db.get(UploadedFile, snapshot.uploaded_file_id)
    assert uploaded is not None
    uploaded.import_status = ImportStatus.PROCESSING.value

    job = ImportJob(
        import_snapshot_id=snapshot.id,
        job_type=JobType.NORMALIZE.value,
        status=JobStatus.RUNNING.value,
        current_stage="normalize",
        progress_percentage=Decimal("5"),
        started_at=datetime.now(UTC),
        idempotency_key=f"normalize:{snapshot.id}",
    )
    db.add(job)
    db.flush()

    storage = get_storage()
    data = storage.get_bytes(uploaded.storage_key)
    workbook = extract_workbook(uploaded.original_filename, data)
    result = FileInterpretationResult.model_validate(
        {
            "source_type": interpretation.source_type,
            "selected_sheet": interpretation.selected_worksheet,
            "header_row": interpretation.header_row or 0,
            "data_start_row": interpretation.data_start_row or 1,
            "data_end_row": interpretation.data_end_row,
            "ignored_rows": interpretation.ignored_rows or [],
            "columns": interpretation.column_mappings,
            "amount_convention": interpretation.amount_convention or "requires_review",
            "date_format": interpretation.date_format,
            "default_currency": interpretation.default_currency or household.default_currency,
            "description_template": interpretation.description_template or "{description}",
            "warnings": interpretation.warnings or [],
            "overall_confidence": float(interpretation.confidence or 0),
        }
    )

    sheet = next(
        (s for s in workbook["sheets"] if s["name"] == result.selected_sheet),
        workbook["sheets"][0],
    )
    rows = sheet["rows"]
    headers = [str(c).strip() if c is not None else f"col_{i}" for i, c in enumerate(rows[result.header_row])]
    mapping = {c.source_column: c.normalized_field for c in result.columns}

    counts = {
        "new": 0,
        "unchanged": 0,
        "updated": 0,
        "possible_duplicate": 0,
        "conflict": 0,
        "failed": 0,
        "duplicate_within_file": 0,
    }
    seen_keys: set[str] = set()
    categories = _load_category_context(db, household.id)
    llm = get_llm_provider(household)

    data_end = result.data_end_row if result.data_end_row is not None else len(rows) - 1
    for row_number in range(result.data_start_row, data_end + 1):
        if row_number in set(result.ignored_rows):
            continue
        if row_number >= len(rows):
            break
        row = rows[row_number]
        if not nonempty_row(row):
            continue
        original = {
            headers[i] if i < len(headers) else f"col_{i}": row[i] if i < len(row) else ""
            for i in range(len(headers))
        }
        raw = RawSourceRow(
            import_snapshot_id=snapshot.id,
            uploaded_file_id=uploaded.id,
            worksheet_name=sheet["name"],
            table_identifier="main",
            source_row_number=row_number,
            original_values={k: _jsonable(v) for k, v in original.items()},
            row_fingerprint=row_fingerprint({k: _jsonable(v) for k, v in original.items()}),
            parsing_status="parsed",
        )
        db.add(raw)
        db.flush()

        try:
            normalized = _normalize_row(original, mapping, result)
        except Exception as exc:  # intentional: capture row failure without aborting import
            # Spec says avoid swallowing errors silently — we persist failure on the row.
            raw.parsing_status = "failed"
            raw.parsing_error = str(exc)
            raw.classification = RowClassification.CONFLICT.value
            counts["failed"] += 1
            continue

        key = stable_source_key(
            source_type=result.source_type,
            account_or_group=str(snapshot.financial_account_id or ""),
            transaction_date=normalized.get("transaction_date"),
            posted_date=normalized.get("posted_date"),
            description=normalized.get("description"),
            currency=normalized.get("currency"),
            reference=normalized.get("reference"),
            signed_amount=normalized.get("signed_amount"),
            native_source_id=normalized.get("reference"),
        )
        if key in seen_keys:
            raw.classification = RowClassification.DUPLICATE_WITHIN_FILE.value
            counts["duplicate_within_file"] += 1
            continue
        seen_keys.add(key)

        identity_fp = canonical_identity_fingerprint(
            source_type=result.source_type,
            account_or_group=str(snapshot.financial_account_id or ""),
            transaction_date=normalized.get("transaction_date"),
            description=normalized.get("description"),
            currency=normalized.get("currency"),
            reference=normalized.get("reference"),
            signed_amount=normalized.get("signed_amount"),
            native_source_id=normalized.get("reference"),
        )
        content_fp = content_fingerprint(normalized)

        existing = db.scalar(
            select(SourceRecord).where(
                SourceRecord.household_id == household.id,
                SourceRecord.source_type == result.source_type,
                SourceRecord.stable_source_key == key,
            )
        )
        if existing and existing.content_fingerprint == content_fp:
            existing.last_seen_snapshot_id = snapshot.id
            existing.last_imported_at = datetime.now(UTC)
            existing.current_source_status = SourceRecordStatus.ACTIVE.value
            raw.source_record_id = existing.id
            raw.classification = RowClassification.UNCHANGED.value
            counts["unchanged"] += 1
            continue

        if existing and existing.content_fingerprint != content_fp:
            existing.source_revision_number += 1
            existing.content_fingerprint = content_fp
            existing.latest_raw_data = normalized
            existing.last_seen_snapshot_id = snapshot.id
            existing.last_imported_at = datetime.now(UTC)
            db.add(
                SourceRecordVersion(
                    source_record_id=existing.id,
                    import_snapshot_id=snapshot.id,
                    revision_number=existing.source_revision_number,
                    content_fingerprint=content_fp,
                    raw_data=normalized,
                    field_differences={"updated": True},
                )
            )
            raw.source_record_id = existing.id
            raw.classification = RowClassification.UPDATED.value
            counts["updated"] += 1
            event = _get_primary_event(db, existing.id)
            if event and not event.is_category_user_confirmed:
                _apply_categorization(db, household, event, existing, categories, llm)
            continue

        source = SourceRecord(
            household_id=household.id,
            source_type=result.source_type,
            source_scope=str(snapshot.financial_account_id or ""),
            native_source_id=normalized.get("reference"),
            stable_source_key=key,
            canonical_identity_fingerprint=identity_fp,
            content_fingerprint=content_fp,
            first_seen_snapshot_id=snapshot.id,
            last_seen_snapshot_id=snapshot.id,
            first_imported_at=datetime.now(UTC),
            last_imported_at=datetime.now(UTC),
            source_revision_number=1,
            current_source_status=SourceRecordStatus.ACTIVE.value,
            latest_raw_data=normalized,
            financial_account_id=snapshot.financial_account_id,
        )
        db.add(source)
        db.flush()
        db.add(
            SourceRecordVersion(
                source_record_id=source.id,
                import_snapshot_id=snapshot.id,
                revision_number=1,
                content_fingerprint=content_fp,
                raw_data=normalized,
                field_differences=None,
            )
        )
        raw.source_record_id = source.id
        raw.classification = RowClassification.NEW.value
        counts["new"] += 1

        event = CanonicalFinancialEvent(
            household_id=household.id,
            event_date=parse_date(normalized.get("transaction_date") or normalized.get("posted_date")),
            posted_date=parse_date(normalized.get("posted_date") or normalized.get("transaction_date")),
            event_type=EventType.UNKNOWN.value,
            confirmed_description=normalize_description(normalized.get("description")) or None,
            original_description=normalized.get("description"),
            confirmed_amount=normalized.get("signed_amount"),
            confirmed_currency=normalized.get("currency") or household.default_currency,
            original_currency=normalized.get("currency") or household.default_currency,
            original_amount=normalized.get("signed_amount"),
            financial_account_id=snapshot.financial_account_id,
            household_economic_share=normalized.get("signed_amount"),
            transaction_direction=_direction(normalized.get("signed_amount")),
            analytics_inclusion_status=AnalyticsInclusionStatus.PENDING.value,
            overall_assessment_status=OverallAssessmentStatus.PROCESSING.value,
            ownership_allocation={"type": "household", "allocations": []},
        )
        # Transfer heuristic before categorization
        if _looks_transfer(normalized.get("description")):
            event.event_type = EventType.TRANSFER.value
            event.transfer_status = "likely"
        db.add(event)
        db.flush()
        db.add(
            SourceEventRelationship(
                source_record_id=source.id,
                canonical_financial_event_id=event.id,
                relationship_type=RelationshipType.PRIMARY_PAYMENT_EVIDENCE.value,
                allocated_amount=normalized.get("signed_amount"),
                match_confidence=Decimal("1.0"),
                match_method="new_import",
                status="confirmed",
                confirmed_by=user.id,
                confirmed_at=datetime.now(UTC),
            )
        )
        _apply_categorization(db, household, event, source, categories, llm)
        event.overall_assessment_status = compute_overall_status(event)
        if event.overall_assessment_status == OverallAssessmentStatus.ASSESSED.value:
            event.analytics_inclusion_status = AnalyticsInclusionStatus.INCLUDED.value

    snapshot.new_record_count = counts["new"]
    snapshot.unchanged_record_count = counts["unchanged"]
    snapshot.updated_record_count = counts["updated"]
    snapshot.possible_duplicate_count = counts["possible_duplicate"]
    snapshot.conflict_count = counts["conflict"]
    snapshot.failed_row_count = counts["failed"]
    snapshot.source_row_count = sum(counts.values())
    snapshot.import_status = ImportStatus.COMPLETED.value
    snapshot.completed_at = datetime.now(UTC)
    uploaded.import_status = ImportStatus.COMPLETED.value
    job.status = JobStatus.COMPLETED.value
    job.progress_percentage = Decimal("100")
    job.processed_row_count = snapshot.source_row_count
    job.source_row_count = snapshot.source_row_count
    job.completed_at = datetime.now(UTC)
    job.current_stage = "completed"
    job.warning_details = {"duplicate_within_file": counts["duplicate_within_file"]}

    record_audit(
        db,
        household_id=household.id,
        user_id=user.id,
        action="import.confirmed",
        entity_type="import_snapshot",
        entity_id=snapshot.id,
        new_value=counts,
    )
    db.commit()
    return import_summary(db, snapshot)


def import_summary(db: Session, snapshot: ImportSnapshot) -> dict[str, Any]:
    interpretation = db.scalar(
        select(ImportInterpretation).where(ImportInterpretation.import_snapshot_id == snapshot.id)
    )
    return {
        "import_snapshot_id": str(snapshot.id),
        "import_status": snapshot.import_status,
        "source_row_count": snapshot.source_row_count,
        "new_record_count": snapshot.new_record_count,
        "unchanged_record_count": snapshot.unchanged_record_count,
        "updated_record_count": snapshot.updated_record_count,
        "possible_duplicate_count": snapshot.possible_duplicate_count,
        "conflict_count": snapshot.conflict_count,
        "failed_row_count": snapshot.failed_row_count,
        "missing_record_count": snapshot.missing_record_count,
        "interpretation": serialize_interpretation(interpretation) if interpretation else None,
    }


def serialize_interpretation(interpretation: ImportInterpretation | None) -> dict[str, Any] | None:
    if not interpretation:
        return None
    return {
        "id": str(interpretation.id),
        "import_snapshot_id": str(interpretation.import_snapshot_id),
        "source_type": interpretation.source_type,
        "selected_worksheet": interpretation.selected_worksheet,
        "header_row": interpretation.header_row,
        "data_start_row": interpretation.data_start_row,
        "data_end_row": interpretation.data_end_row,
        "ignored_rows": interpretation.ignored_rows,
        "column_mappings": interpretation.column_mappings,
        "date_format": interpretation.date_format,
        "amount_convention": interpretation.amount_convention,
        "default_currency": interpretation.default_currency,
        "description_template": interpretation.description_template,
        "confidence": str(interpretation.confidence) if interpretation.confidence is not None else None,
        "warnings": interpretation.warnings,
        "sample_normalized_rows": interpretation.sample_normalized_rows,
        "is_human_confirmed": interpretation.is_human_confirmed,
        "prompt_version": interpretation.prompt_version,
        "llm_provider": interpretation.llm_provider,
        "llm_model": interpretation.llm_model,
        "structural_summary": interpretation.structural_summary,
    }


def _preview_normalized_rows(
    workbook: dict[str, Any],
    result: FileInterpretationResult,
    limit: int,
) -> list[dict[str, Any]]:
    sheet = next(
        (s for s in workbook["sheets"] if s["name"] == result.selected_sheet),
        workbook["sheets"][0],
    )
    rows = sheet["rows"]
    headers = [str(c).strip() if c is not None else f"col_{i}" for i, c in enumerate(rows[result.header_row])]
    mapping = {c.source_column: c.normalized_field for c in result.columns}
    samples: list[dict[str, Any]] = []
    data_end = result.data_end_row if result.data_end_row is not None else len(rows) - 1
    for row_number in range(result.data_start_row, data_end + 1):
        if len(samples) >= limit:
            break
        if row_number >= len(rows) or not nonempty_row(rows[row_number]):
            continue
        original = {
            headers[i] if i < len(headers) else f"col_{i}": rows[row_number][i]
            if i < len(rows[row_number])
            else ""
            for i in range(len(headers))
        }
        try:
            samples.append(_normalize_row(original, mapping, result))
        except Exception as exc:
            samples.append({"error": str(exc), "original": {k: _jsonable(v) for k, v in original.items()}})
    return samples


def _normalize_row(
    original: dict[str, Any],
    mapping: dict[str, str],
    result: FileInterpretationResult,
) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "transaction_date": None,
        "posted_date": None,
        "description": None,
        "debit": None,
        "credit": None,
        "signed_amount": None,
        "currency": result.default_currency,
        "reference": None,
        "notes": None,
    }
    for source_col, normalized_field in mapping.items():
        if normalized_field == "ignore":
            continue
        value = original.get(source_col)
        if normalized_field in {"transaction_date", "posted_date"}:
            parsed = parse_date(value, result.date_format)
            fields[normalized_field] = parsed.isoformat() if parsed else None
        elif normalized_field in {"debit", "credit", "signed_amount", "balance", "share"}:
            fields[normalized_field] = parse_decimal(value)
        else:
            fields[normalized_field] = str(value).strip() if value is not None else None

    amount = normalize_signed_amount(
        signed_amount=fields.get("signed_amount"),
        debit=fields.get("debit"),
        credit=fields.get("credit"),
        amount_convention=result.amount_convention,
    )
    fields["signed_amount"] = amount
    if not fields.get("description"):
        fields["description"] = result.description_template
    # Serialize decimals for JSON storage
    return {k: _jsonable(v) for k, v in fields.items()}


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _direction(amount: Decimal | str | None) -> str | None:
    if amount is None:
        return None
    value = Decimal(str(amount))
    if value > 0:
        return "inflow"
    if value < 0:
        return "outflow"
    return "zero"


def _looks_transfer(description: str | None) -> bool:
    if not description:
        return False
    text = description.lower()
    return any(
        token in text
        for token in ("transfer", "xfer", "payment thank you", "autopay", "credit card payment")
    )


def _load_category_context(db: Session, household_id: UUID) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(Category).where(
            (Category.household_id.is_(None)) | (Category.household_id == household_id),
            Category.is_active.is_(True),
        )
    ).all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "parent_id": str(c.parent_category_id) if c.parent_category_id else None,
            "level": c.category_level,
        }
        for c in rows
    ]


def _get_primary_event(db: Session, source_record_id: UUID) -> CanonicalFinancialEvent | None:
    rel = db.scalar(
        select(SourceEventRelationship).where(
            SourceEventRelationship.source_record_id == source_record_id,
            SourceEventRelationship.relationship_type
            == RelationshipType.PRIMARY_PAYMENT_EVIDENCE.value,
        )
    )
    if not rel:
        return None
    return db.get(CanonicalFinancialEvent, rel.canonical_financial_event_id)


def _apply_categorization(
    db: Session,
    household: Household,
    event: CanonicalFinancialEvent,
    source: SourceRecord,
    categories: list[dict[str, Any]],
    llm,
) -> None:
    if event.is_category_user_confirmed:
        return
    context = {
        "transaction_id": str(event.id),
        "description": event.original_description or event.confirmed_description,
        "amount": str(event.confirmed_amount or "0"),
        "direction": event.transaction_direction,
        "currency": event.confirmed_currency,
        "account_type": None,
    }
    result = llm.categorize(context, categories)
    assessment = CategorizationAssessment(
        canonical_financial_event_id=event.id,
        source_record_id=source.id,
        suggested_transaction_type=result.transaction_type,
        suggested_merchant=result.normalized_merchant,
        suggested_category_id=UUID(result.existing_category_id)
        if result.existing_category_id
        else None,
        suggested_subcategory_id=UUID(result.existing_subcategory_id)
        if result.existing_subcategory_id
        else None,
        suggested_ownership_allocation=result.owner_suggestion,
        suggested_recurring_status=result.recurring_suggestion,
        suggested_fixed_or_variable=result.fixed_or_variable,
        suggested_essential_or_discretionary=result.essential_or_discretionary,
        transfer_likelihood=Decimal(str(result.transfer_likelihood)),
        refund_likelihood=Decimal(str(result.refund_likelihood)),
        confidence=Decimal(str(result.confidence)),
        category_fit=result.category_fit,
        decision_method="llm",
        llm_provider=llm.provider_name,
        llm_model=llm.model_name,
        prompt_version="categorize_v1",
        structured_model_output=result.model_dump(),
        explanation=result.reason,
        needs_human_review=result.needs_human_review,
        review_reason=result.review_reason,
    )
    db.add(assessment)

    thresholds = household.assessment_confidence_settings or {}
    auto_accept = Decimal(str(thresholds.get("auto_accept", 0.90)))
    event.llm_confidence = Decimal(str(result.confidence))
    event.event_type = result.transaction_type
    event.confirmed_description = result.normalized_merchant or event.confirmed_description
    event.ownership_allocation = result.owner_suggestion
    event.review_reason = result.review_reason

    if result.transaction_type == "transfer" or result.transfer_likelihood >= 0.9:
        event.transfer_status = "likely"
        event.event_type = EventType.TRANSFER.value

    if result.propose_new_category and result.proposed_category:
        proposal = CategoryProposal(
            household_id=household.id,
            proposed_name=result.proposed_category.get("name") or "New Category",
            proposed_parent_category_id=UUID(result.proposed_category["parent_id"])
            if result.proposed_category.get("parent_id")
            else None,
            proposed_category_level=int(result.proposed_category.get("level") or 2),
            proposed_description=result.proposed_category.get("description"),
            reason_existing_insufficient=result.reason,
            example_event_ids=[str(event.id)],
            affected_event_count=1,
            total_amount_affected=abs(event.confirmed_amount or Decimal("0")),
            llm_provider=llm.provider_name,
            llm_model=llm.model_name,
            prompt_version="categorize_v1",
            confidence=Decimal(str(result.confidence)),
            status="pending",
        )
        db.add(proposal)
        event.overall_assessment_status = OverallAssessmentStatus.PENDING_CATEGORY.value
        event.analytics_inclusion_status = AnalyticsInclusionStatus.PENDING.value
        return

    # Validate category IDs against household/system categories
    valid_ids = {c["id"] for c in categories}
    cat_id = result.existing_category_id if result.existing_category_id in valid_ids else None
    sub_id = result.existing_subcategory_id if result.existing_subcategory_id in valid_ids else None
    confidence = Decimal(str(result.confidence))

    if cat_id and confidence >= auto_accept and not result.needs_human_review:
        event.confirmed_category_id = UUID(cat_id)
        event.confirmed_subcategory_id = UUID(sub_id) if sub_id else None
        assessment.accepted_at = datetime.now(UTC)
        if event.event_type == EventType.TRANSFER.value:
            event.analytics_inclusion_status = AnalyticsInclusionStatus.EXCLUDED.value
        else:
            event.analytics_inclusion_status = AnalyticsInclusionStatus.INCLUDED.value
    else:
        event.confirmed_category_id = UUID(cat_id) if cat_id else None
        event.confirmed_subcategory_id = UUID(sub_id) if sub_id else None
        event.overall_assessment_status = OverallAssessmentStatus.PENDING_CATEGORY.value
        event.analytics_inclusion_status = AnalyticsInclusionStatus.PENDING.value
