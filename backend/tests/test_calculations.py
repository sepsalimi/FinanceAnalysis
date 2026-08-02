"""Unit tests for documented financial calculations."""

from decimal import Decimal

import pytest

from app.core.config import normalize_database_url
from app.services.calculations import (
    amount_within_splitwise_tolerance,
    annualize,
    assessment_completion_pct,
    net_cash_flow,
    savings_rate,
    splits_sum_to_amount,
)
from app.services.fingerprints import (
    canonical_identity_fingerprint,
    content_fingerprint,
    stable_source_key,
)
from app.services.money import normalize_signed_amount, parse_date, parse_decimal


def test_normalize_database_url():
    assert normalize_database_url("postgres://u:p@h/db").startswith("postgresql+psycopg://")
    assert normalize_database_url("postgresql://u:p@h/db").startswith("postgresql+psycopg://")
    assert (
        normalize_database_url("postgresql+psycopg://u:p@h/db")
        == "postgresql+psycopg://u:p@h/db"
    )


def test_annualize_monthly():
    assert annualize(Decimal("100"), "monthly") == Decimal("1200")


def test_savings_rate_zero_income():
    assert savings_rate(Decimal("0"), Decimal("10")) is None


def test_savings_rate_normal():
    assert savings_rate(Decimal("1000"), Decimal("200")) == Decimal("0.2")


def test_net_cash_flow():
    assert net_cash_flow(Decimal("1000"), Decimal("-400")) == Decimal("600")


def test_assessment_completion():
    assert assessment_completion_pct(198, 245) == Decimal("80.8")


def test_splits_validation():
    assert splits_sum_to_amount([Decimal("10"), Decimal("5")], Decimal("15"))


def test_splitwise_tolerance():
    assert amount_within_splitwise_tolerance(Decimal("50"), Decimal("58"))
    assert not amount_within_splitwise_tolerance(Decimal("50"), Decimal("70"))


def test_parse_decimal_and_date():
    assert parse_decimal("($12.50)") == Decimal("-12.50")
    assert parse_date("2024-01-15").isoformat() == "2024-01-15"


def test_amount_conventions():
    assert normalize_signed_amount(
        signed_amount=Decimal("20"),
        debit=None,
        credit=None,
        amount_convention="expenses_positive",
    ) == Decimal("-20")
    assert normalize_signed_amount(
        signed_amount=None,
        debit=Decimal("15"),
        credit=None,
        amount_convention="separate_debit_credit",
    ) == Decimal("-15")


def test_fingerprints_stable():
    key1 = stable_source_key(
        source_type="bank_statement",
        account_or_group="acct",
        transaction_date="2024-01-01",
        posted_date="2024-01-01",
        description="Coffee Shop",
        currency="CAD",
        reference=None,
        signed_amount=Decimal("-4.50"),
    )
    key2 = stable_source_key(
        source_type="bank_statement",
        account_or_group="acct",
        transaction_date="2024-01-01",
        posted_date="2024-01-01",
        description="coffee shop",
        currency="CAD",
        reference=None,
        signed_amount=Decimal("-4.50"),
    )
    assert key1 == key2
    assert canonical_identity_fingerprint(
        source_type="bank_statement",
        account_or_group="acct",
        transaction_date="2024-01-01",
        description="Coffee Shop",
        currency="CAD",
        reference=None,
        signed_amount=Decimal("-4.50"),
    )
    assert content_fingerprint({"a": 1, "b": "x"}) != content_fingerprint({"a": 2, "b": "x"})
