"""Upload, snapshot, interpretation, raw row, and source record models."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    FileType,
    ImportStatus,
    JobStatus,
    JobType,
    MalwareScanStatus,
    SourceRecordStatus,
    SourceType,
)


class UploadedFile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "uploaded_files"

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    uploaded_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user_accounts.id", ondelete="SET NULL")
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), default=FileType.UNKNOWN.value)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    detected_source_type: Mapped[str] = mapped_column(
        String(64), default=SourceType.UNKNOWN.value
    )
    import_status: Mapped[str] = mapped_column(
        String(64), default=ImportStatus.UPLOADED.value, index=True
    )
    malware_scan_status: Mapped[str] = mapped_column(
        String(64), default=MalwareScanStatus.SKIPPED.value
    )
    deletion_status: Mapped[str] = mapped_column(String(32), default="active")


class ImportSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "import_snapshots"

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    uploaded_file_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("uploaded_files.id", ondelete="CASCADE"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(64), default=SourceType.UNKNOWN.value)
    source_scope: Mapped[str | None] = mapped_column(String(200))
    financial_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("financial_accounts.id", ondelete="SET NULL")
    )
    splitwise_group: Mapped[str | None] = mapped_column(String(200))
    export_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    earliest_source_date: Mapped[date | None] = mapped_column(Date)
    latest_source_date: Mapped[date | None] = mapped_column(Date)
    source_row_count: Mapped[int] = mapped_column(Integer, default=0)
    new_record_count: Mapped[int] = mapped_column(Integer, default=0)
    unchanged_record_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_record_count: Mapped[int] = mapped_column(Integer, default=0)
    possible_duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    conflict_count: Mapped[int] = mapped_column(Integer, default=0)
    missing_record_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_row_count: Mapped[int] = mapped_column(Integer, default=0)
    import_status: Mapped[str] = mapped_column(
        String(64), default=ImportStatus.PENDING.value, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ImportJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "import_jobs"

    import_snapshot_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("import_snapshots.id", ondelete="CASCADE"), index=True
    )
    job_type: Mapped[str] = mapped_column(String(64), default=JobType.INTERPRET.value)
    status: Mapped[str] = mapped_column(String(64), default=JobStatus.QUEUED.value, index=True)
    current_stage: Mapped[str | None] = mapped_column(String(100))
    progress_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    source_row_count: Mapped[int] = mapped_column(Integer, default=0)
    processed_row_count: Mapped[int] = mapped_column(Integer, default=0)
    error_details: Mapped[dict | None] = mapped_column(JSONB)
    warning_details: Mapped[dict | None] = mapped_column(JSONB)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    idempotency_key: Mapped[str | None] = mapped_column(String(200), index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)


class ImportInterpretation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "import_interpretations"

    import_snapshot_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("import_snapshots.id", ondelete="CASCADE"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(64), default=SourceType.UNKNOWN.value)
    selected_worksheet: Mapped[str | None] = mapped_column(String(200))
    selected_table_range: Mapped[str | None] = mapped_column(String(100))
    header_row: Mapped[int | None] = mapped_column(Integer)
    data_start_row: Mapped[int | None] = mapped_column(Integer)
    data_end_row: Mapped[int | None] = mapped_column(Integer)
    ignored_rows: Mapped[list] = mapped_column(JSONB, default=list)
    column_mappings: Mapped[list] = mapped_column(JSONB, default=list)
    date_format: Mapped[str | None] = mapped_column(String(64))
    amount_convention: Mapped[str | None] = mapped_column(String(64))
    default_currency: Mapped[str | None] = mapped_column(String(3))
    description_template: Mapped[str | None] = mapped_column(String(500))
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    warnings: Mapped[list] = mapped_column(JSONB, default=list)
    sample_normalized_rows: Mapped[list] = mapped_column(JSONB, default=list)
    structural_summary: Mapped[dict | None] = mapped_column(JSONB)
    is_human_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    prompt_version: Mapped[str | None] = mapped_column(String(64))
    llm_provider: Mapped[str | None] = mapped_column(String(64))
    llm_model: Mapped[str | None] = mapped_column(String(128))


class ImportProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "import_profiles"

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    source_name: Mapped[str] = mapped_column(String(200), nullable=False)
    institution_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    financial_account_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    structural_signature: Mapped[str] = mapped_column(String(128), index=True)
    mapping_configuration: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RawSourceRow(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "raw_source_rows"
    __table_args__ = (
        UniqueConstraint(
            "import_snapshot_id",
            "worksheet_name",
            "source_row_number",
            name="uq_raw_row_snapshot_sheet_num",
        ),
    )

    import_snapshot_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("import_snapshots.id", ondelete="CASCADE"), index=True
    )
    uploaded_file_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("uploaded_files.id", ondelete="CASCADE")
    )
    worksheet_name: Mapped[str | None] = mapped_column(String(200))
    table_identifier: Mapped[str | None] = mapped_column(String(100))
    source_row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    original_values: Mapped[dict] = mapped_column(JSONB, nullable=False)
    row_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    parsing_status: Mapped[str] = mapped_column(String(64), default="pending")
    parsing_error: Mapped[str | None] = mapped_column(Text)
    classification: Mapped[str | None] = mapped_column(String(64))
    source_record_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("source_records.id", ondelete="SET NULL"), index=True
    )


class SourceRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "source_records"
    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "source_type",
            "stable_source_key",
            name="uq_source_record_stable_key",
        ),
    )

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_scope: Mapped[str | None] = mapped_column(String(200))
    native_source_id: Mapped[str | None] = mapped_column(String(200), index=True)
    stable_source_key: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_identity_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    content_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    first_seen_snapshot_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    last_seen_snapshot_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    first_imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_revision_number: Mapped[int] = mapped_column(Integer, default=1)
    current_source_status: Mapped[str] = mapped_column(
        String(64), default=SourceRecordStatus.ACTIVE.value, index=True
    )
    latest_raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    deleted_at_source: Mapped[bool] = mapped_column(Boolean, default=False)
    financial_account_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)


class SourceRecordVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "source_record_versions"

    source_record_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("source_records.id", ondelete="CASCADE"), index=True
    )
    import_snapshot_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    field_differences: Mapped[dict | None] = mapped_column(JSONB)
