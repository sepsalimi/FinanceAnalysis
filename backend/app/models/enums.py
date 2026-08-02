"""Shared enumerations for domain models."""

import enum


class MembershipRole(str, enum.Enum):
    OWNER = "owner"
    ADMINISTRATOR = "administrator"
    MEMBER = "member"
    READ_ONLY = "read_only"


class MemberProfileRole(str, enum.Enum):
    FINANCIAL_PARTICIPANT = "financial_participant"
    LOGIN_USER = "login_user"
    HOUSEHOLD_ADMINISTRATOR = "household_administrator"
    READ_ONLY_USER = "read_only_user"
    INACTIVE_HISTORICAL = "inactive_historical"


class AccountType(str, enum.Enum):
    CHEQUING = "chequing"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    LINE_OF_CREDIT = "line_of_credit"
    LOAN = "loan"
    MORTGAGE = "mortgage"
    INVESTMENT = "investment"
    CASH = "cash"
    OTHER = "other"


class InstitutionType(str, enum.Enum):
    BANK = "bank"
    CREDIT_UNION = "credit_union"
    CREDIT_CARD_ISSUER = "credit_card_issuer"
    BROKERAGE = "brokerage"
    LENDER = "lender"
    OTHER = "other"


class FileType(str, enum.Enum):
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"
    UNKNOWN = "unknown"


class SourceType(str, enum.Enum):
    BANK_STATEMENT = "bank_statement"
    CREDIT_CARD_STATEMENT = "credit_card_statement"
    SPLITWISE = "splitwise"
    HOUSEHOLD_WORKBOOK = "household_workbook"
    UNKNOWN = "unknown"


class ImportStatus(str, enum.Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    INTERPRETING = "interpreting"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class MalwareScanStatus(str, enum.Enum):
    NOT_SCANNED = "not_scanned"
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class JobType(str, enum.Enum):
    INTERPRET = "interpret"
    NORMALIZE = "normalize"
    CATEGORIZE = "categorize"
    SPLITWISE_MATCH = "splitwise_match"
    ANALYTICS = "analytics"
    EXPORT = "export"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class SourceRecordStatus(str, enum.Enum):
    ACTIVE = "active"
    MISSING_FROM_LATEST_SNAPSHOT = "missing_from_latest_snapshot"
    DELETED_AT_SOURCE = "deleted_at_source"
    REAPPEARED = "reappeared"
    SUPERSEDED = "superseded"
    ERROR = "error"


class EventType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    DEBT_REPAYMENT = "debt_repayment"
    REFUND = "refund"
    REIMBURSEMENT = "reimbursement"
    INVESTMENT_CONTRIBUTION = "investment_contribution"
    INVESTMENT_WITHDRAWAL = "investment_withdrawal"
    ADJUSTMENT = "adjustment"
    UNKNOWN = "unknown"


class RelationshipType(str, enum.Enum):
    PRIMARY_PAYMENT_EVIDENCE = "primary_payment_evidence"
    SHARED_EXPENSE_ALLOCATION_EVIDENCE = "shared_expense_allocation_evidence"
    REIMBURSEMENT_EVIDENCE = "reimbursement_evidence"
    TRANSFER_EVIDENCE = "transfer_evidence"
    PLANNING_RECORD = "planning_record"
    PARTIAL_EVENT = "partial_event"
    COMBINED_EVENT = "combined_event"
    POSSIBLE_OVERLAP = "possible_overlap"
    REJECTED_RELATIONSHIP = "rejected_relationship"


class MatchStatus(str, enum.Enum):
    SUGGESTED = "suggested"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class OverallAssessmentStatus(str, enum.Enum):
    IMPORTED = "imported"
    PROCESSING = "processing"
    ASSESSED = "assessed"
    ASSESSED_WITH_WARNING = "assessed_with_warning"
    NEEDS_REVIEW = "needs_review"
    PENDING_CATEGORY = "pending_category"
    PENDING_MATCH = "pending_match"
    UNASSESSED = "unassessed"
    EXCLUDED = "excluded"
    FAILED = "failed"


class CategoryProposalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    MAPPED_TO_EXISTING = "mapped_to_existing"
    RENAMED_AND_APPROVED = "renamed_and_approved"
    REJECTED = "rejected"


class AnalyticsInclusionStatus(str, enum.Enum):
    INCLUDED = "included"
    EXCLUDED = "excluded"
    PENDING = "pending"


class Frequency(str, enum.Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    SEMIMONTHLY = "semimonthly"
    MONTHLY = "monthly"
    EVERY_TWO_MONTHS = "every_two_months"
    QUARTERLY = "quarterly"
    SEMIANNUALLY = "semiannually"
    ANNUALLY = "annually"
    CUSTOM_INTERVAL = "custom_interval"


class PlannedItemStatus(str, enum.Enum):
    PLANNED = "planned"
    PARTIALLY_COMPLETED = "partially_completed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class RowClassification(str, enum.Enum):
    NEW = "new"
    UNCHANGED = "unchanged"
    UPDATED = "updated"
    POSSIBLE_DUPLICATE = "possible_duplicate"
    CONFLICT = "conflict"
    REAPPEARED = "reappeared"
    DELETED_AT_SOURCE = "deleted_at_source"
    MISSING_FROM_SNAPSHOT = "missing_from_snapshot"
    DUPLICATE_WITHIN_FILE = "duplicate_within_file"
