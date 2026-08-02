"""Canonical identity and content fingerprint helpers for import identity."""

import hashlib
import json
import re
from decimal import Decimal
from typing import Any


def normalize_description(value: str | None) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"\s+", " ", value.strip().lower())
    cleaned = re.sub(r"[^a-z0-9 #*/&\-_.]", "", cleaned)
    return cleaned


def _stable_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def row_fingerprint(original_values: dict[str, Any]) -> str:
    return sha256_text(_stable_dumps(original_values))


def stable_source_key(
    *,
    source_type: str,
    account_or_group: str | None,
    transaction_date: str | None,
    posted_date: str | None,
    description: str | None,
    currency: str | None,
    reference: str | None,
    signed_amount: Decimal | None,
    native_source_id: str | None = None,
) -> str:
    if native_source_id:
        material = {
            "source_type": source_type,
            "scope": account_or_group or "",
            "native_source_id": native_source_id,
        }
    else:
        material = {
            "source_type": source_type,
            "scope": account_or_group or "",
            "transaction_date": transaction_date or "",
            "posted_date": posted_date or "",
            "description": normalize_description(description),
            "currency": (currency or "").upper(),
            "reference": reference or "",
            "signed_amount": str(signed_amount) if signed_amount is not None else "",
        }
    return sha256_text(_stable_dumps(material))


def canonical_identity_fingerprint(
    *,
    source_type: str,
    account_or_group: str | None,
    transaction_date: str | None,
    description: str | None,
    currency: str | None,
    reference: str | None,
    signed_amount: Decimal | None,
    native_source_id: str | None = None,
) -> str:
    material = {
        "source_type": source_type,
        "scope": account_or_group or "",
        "native_source_id": native_source_id or "",
        "transaction_date": transaction_date or "",
        "description": normalize_description(description),
        "currency": (currency or "").upper(),
        "reference": reference or "",
        "signed_amount": str(signed_amount) if signed_amount is not None else "",
    }
    return sha256_text(_stable_dumps(material))


def content_fingerprint(normalized_fields: dict[str, Any]) -> str:
    return sha256_text(_stable_dumps(normalized_fields))
