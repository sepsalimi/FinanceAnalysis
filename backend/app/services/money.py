"""Amount and date normalization utilities."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from dateutil import parser as date_parser


def parse_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    text = str(value).strip()
    text = text.replace(",", "")
    text = text.replace("$", "").replace("€", "").replace("£", "")
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def parse_date(value: Any, date_format: str | None = None) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = str(value).strip()
    if date_format:
        return datetime.strptime(text, date_format).date()
    return date_parser.parse(text, dayfirst=False).date()


def normalize_signed_amount(
    *,
    signed_amount: Decimal | None,
    debit: Decimal | None,
    credit: Decimal | None,
    amount_convention: str,
) -> Decimal | None:
    if amount_convention == "separate_debit_credit":
        if debit is not None and credit is not None:
            if debit != 0 and credit != 0:
                raise ValueError("Both debit and credit populated")
            if debit and debit != 0:
                return -abs(debit)
            if credit and credit != 0:
                return abs(credit)
            return Decimal("0")
        if debit is not None:
            return -abs(debit)
        if credit is not None:
            return abs(credit)
        return None

    if signed_amount is None:
        return None

    if amount_convention == "expenses_positive":
        # Incoming positive convention flipped to platform convention.
        return -signed_amount
    if amount_convention == "expenses_negative":
        return signed_amount
    if amount_convention == "requires_review":
        return signed_amount
    raise ValueError(f"Unknown amount convention: {amount_convention}")
