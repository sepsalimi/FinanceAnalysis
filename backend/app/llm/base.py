"""LLM provider abstraction and structured output schemas."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.core.config import get_settings


class FileColumnMapping(BaseModel):
    source_column: str
    normalized_field: Literal[
        "posted_date",
        "transaction_date",
        "description",
        "debit",
        "credit",
        "signed_amount",
        "balance",
        "currency",
        "reference",
        "payer",
        "participant",
        "share",
        "category_hint",
        "notes",
        "ignore",
    ]
    confidence: float = Field(ge=0, le=1)
    reason: str


class FileInterpretationResult(BaseModel):
    source_type: Literal[
        "bank_statement",
        "credit_card_statement",
        "splitwise",
        "household_workbook",
        "unknown",
    ]
    institution_or_source: str | None = None
    selected_sheet: str | None = None
    header_row: int = 0
    data_start_row: int = 1
    data_end_row: int | None = None
    ignored_rows: list[int] = Field(default_factory=list)
    columns: list[FileColumnMapping]
    amount_convention: Literal[
        "expenses_negative",
        "expenses_positive",
        "separate_debit_credit",
        "requires_review",
    ]
    date_format: str | None = None
    default_currency: str
    description_template: str = "{description}"
    warnings: list[str] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0, le=1)


class CategorizationResult(BaseModel):
    transaction_id: str
    normalized_merchant: str | None = None
    transaction_type: Literal[
        "income",
        "expense",
        "transfer",
        "debt_repayment",
        "refund",
        "investment_contribution",
        "investment_withdrawal",
        "reimbursement",
        "adjustment",
        "unknown",
    ]
    existing_category_id: str | None = None
    existing_subcategory_id: str | None = None
    existing_category_name: str | None = None
    existing_subcategory_name: str | None = None
    category_fit: Literal["strong", "acceptable", "weak", "no_existing_match"]
    propose_new_category: bool = False
    proposed_category: dict[str, Any] | None = None
    owner_suggestion: dict[str, Any] = Field(
        default_factory=lambda: {"allocation_type": "household", "allocations": []}
    )
    recurring_suggestion: bool = False
    fixed_or_variable: Literal["fixed", "variable", "unknown"] = "unknown"
    essential_or_discretionary: Literal["essential", "discretionary", "mixed", "unknown"] = "unknown"
    transfer_likelihood: float = Field(ge=0, le=1, default=0)
    refund_likelihood: float = Field(ge=0, le=1, default=0)
    confidence: float = Field(ge=0, le=1)
    reason: str
    needs_human_review: bool = False
    review_reason: str | None = None


class LLMProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    def interpret_file(self, structural_summary: dict[str, Any]) -> FileInterpretationResult:
        raise NotImplementedError

    @abstractmethod
    def categorize(
        self,
        event_context: dict[str, Any],
        categories: list[dict[str, Any]],
    ) -> CategorizationResult:
        raise NotImplementedError


class StubLLMProvider(LLMProvider):
    """Deterministic offline provider for local development and tests."""

    provider_name = "stub"
    model_name = "stub-v1"

    def interpret_file(self, structural_summary: dict[str, Any]) -> FileInterpretationResult:
        headers = structural_summary.get("headers") or []
        columns: list[FileColumnMapping] = []
        amount_convention = "expenses_negative"
        for header in headers:
            key = str(header).strip().lower()
            field = "ignore"
            conf = 0.55
            reason = "No strong heuristic match"
            if key in {"date", "transaction date", "trans date", "posted date"}:
                field = "posted_date" if "posted" in key else "transaction_date"
                conf = 0.95
                reason = "Header looks like a date column"
            elif key in {"description", "memo", "details", "narrative", "name"}:
                field = "description"
                conf = 0.93
                reason = "Header looks like a description column"
            elif key in {"amount", "transaction amount", "value"}:
                field = "signed_amount"
                conf = 0.9
                reason = "Single amount column"
            elif key in {"debit", "withdrawal", "money out"}:
                field = "debit"
                conf = 0.92
                reason = "Debit column"
                amount_convention = "separate_debit_credit"
            elif key in {"credit", "deposit", "money in"}:
                field = "credit"
                conf = 0.92
                reason = "Credit column"
                amount_convention = "separate_debit_credit"
            elif key in {"balance", "running balance"}:
                field = "balance"
                conf = 0.85
                reason = "Balance column"
            elif key in {"currency", "ccy"}:
                field = "currency"
                conf = 0.88
                reason = "Currency column"
            elif key in {"reference", "ref", "transaction id", "id"}:
                field = "reference"
                conf = 0.8
                reason = "Reference column"
            columns.append(
                FileColumnMapping(
                    source_column=str(header),
                    normalized_field=field,  # type: ignore[arg-type]
                    confidence=conf,
                    reason=reason,
                )
            )
        currency = structural_summary.get("default_currency") or "USD"
        source_type = structural_summary.get("guessed_source_type") or "bank_statement"
        return FileInterpretationResult(
            source_type=source_type,
            institution_or_source=structural_summary.get("institution_or_source"),
            selected_sheet=structural_summary.get("selected_sheet"),
            header_row=int(structural_summary.get("header_row") or 0),
            data_start_row=int(structural_summary.get("data_start_row") or 1),
            data_end_row=structural_summary.get("data_end_row"),
            ignored_rows=structural_summary.get("ignored_rows") or [],
            columns=columns,
            amount_convention=amount_convention,  # type: ignore[arg-type]
            date_format=structural_summary.get("date_format"),
            default_currency=currency,
            description_template="{description}",
            warnings=structural_summary.get("warnings") or [],
            overall_confidence=0.82,
        )

    def categorize(
        self,
        event_context: dict[str, Any],
        categories: list[dict[str, Any]],
    ) -> CategorizationResult:
        description = (event_context.get("description") or "").lower()
        amount = Decimal(str(event_context.get("amount") or "0"))
        event_id = str(event_context["transaction_id"])

        def find_cat(*names: str) -> tuple[str | None, str | None, str | None, str | None]:
            for cat in categories:
                if cat["name"].lower() in {n.lower() for n in names} and cat.get("parent_id"):
                    parent = next((c for c in categories if c["id"] == cat["parent_id"]), None)
                    return cat["parent_id"], cat["id"], parent["name"] if parent else None, cat["name"]
                if cat["name"].lower() in {n.lower() for n in names} and not cat.get("parent_id"):
                    return cat["id"], None, cat["name"], None
            return None, None, None, None

        transfer_tokens = ("transfer", "xfer", "payment thank you", "autopay", "credit card payment")
        if any(t in description for t in transfer_tokens):
            parent_id, sub_id, parent_name, sub_name = find_cat("Account Transfer", "Transfers")
            return CategorizationResult(
                transaction_id=event_id,
                normalized_merchant="Transfer",
                transaction_type="transfer",
                existing_category_id=parent_id,
                existing_subcategory_id=sub_id,
                existing_category_name=parent_name,
                existing_subcategory_name=sub_name,
                category_fit="strong" if parent_id else "weak",
                transfer_likelihood=0.95,
                confidence=0.91,
                reason="Description matches transfer patterns",
                needs_human_review=False,
            )

        if amount > 0 and any(t in description for t in ("payroll", "salary", "direct deposit", "pay")):
            parent_id, sub_id, parent_name, sub_name = find_cat("Employment Income", "Income")
            return CategorizationResult(
                transaction_id=event_id,
                normalized_merchant="Payroll",
                transaction_type="income",
                existing_category_id=parent_id,
                existing_subcategory_id=sub_id,
                existing_category_name=parent_name,
                existing_subcategory_name=sub_name,
                category_fit="strong" if sub_id or parent_id else "weak",
                confidence=0.9,
                reason="Inflow with payroll-like description",
            )

        grocery_tokens = ("grocery", "supermarket", "whole foods", "trader joe", "costco", "walmart")
        if any(t in description for t in grocery_tokens):
            parent_id, sub_id, parent_name, sub_name = find_cat("Groceries")
            return CategorizationResult(
                transaction_id=event_id,
                normalized_merchant="Grocery store",
                transaction_type="expense",
                existing_category_id=parent_id,
                existing_subcategory_id=sub_id,
                existing_category_name=parent_name,
                existing_subcategory_name=sub_name,
                category_fit="strong" if sub_id or parent_id else "weak",
                confidence=0.88,
                reason="Description matches grocery merchants",
                needs_human_review=True,
                review_reason="Confidence below auto-accept threshold",
            )

        dining_tokens = ("restaurant", "cafe", "coffee", "uber eats", "doordash", "mcdonald", "starbucks")
        if any(t in description for t in dining_tokens):
            parent_id, sub_id, parent_name, sub_name = find_cat(
                "Restaurants", "Fast Food", "Cafes", "Food Delivery", "Dining Out"
            )
            return CategorizationResult(
                transaction_id=event_id,
                normalized_merchant="Dining",
                transaction_type="expense",
                existing_category_id=parent_id,
                existing_subcategory_id=sub_id,
                existing_category_name=parent_name or "Dining Out",
                existing_subcategory_name=sub_name,
                category_fit="strong" if parent_id else "weak",
                confidence=0.86,
                reason="Description matches dining patterns",
                needs_human_review=True,
                review_reason="Confidence below auto-accept threshold",
            )

        parent_id, sub_id, parent_name, sub_name = find_cat("Uncategorized")
        return CategorizationResult(
            transaction_id=event_id,
            normalized_merchant=None,
            transaction_type="expense" if amount < 0 else "unknown",
            existing_category_id=parent_id,
            existing_subcategory_id=sub_id,
            existing_category_name=parent_name,
            existing_subcategory_name=sub_name,
            category_fit="weak",
            confidence=0.45,
            reason="No strong existing category match",
            needs_human_review=True,
            review_reason="Low confidence categorization",
        )


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower()
    if provider == "stub" or not any(
        [settings.openai_api_key, settings.anthropic_api_key, settings.gemini_api_key]
    ):
        return StubLLMProvider()
    # External providers can be wired here without changing call sites.
    return StubLLMProvider()
