"""End-to-end API test for the first complete vertical workflow."""

from decimal import Decimal
from io import BytesIO


def _register_and_login(client, email: str = "person1@example.com"):
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": "Primary User",
        },
    )
    assert reg.status_code == 201, reg.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert login.status_code == 200, login.text
    return login.json()


def test_vertical_import_workflow(client):
    _register_and_login(client)

    onboard = client.post(
        "/api/v1/onboarding",
        json={
            "household_name": "Sample Household",
            "currency": "CAD",
            "timezone": "America/Toronto",
            "people": [
                {"name": "Person 1"},
                {"name": "Person 2"},
                {"name": ""},
            ],
        },
    )
    assert onboard.status_code == 201, onboard.text
    household = onboard.json()
    assert household["default_currency"] == "CAD"

    # Add another member later
    members = client.post(
        f"/api/v1/households/{household['id']}/members",
        json={"display_name": "Person 3"},
    )
    assert members.status_code == 201

    account = client.post(
        "/api/v1/accounts",
        json={
            "account_name": "Everyday Chequing",
            "account_type": "chequing",
            "currency": "CAD",
            "opening_balance": "1000.00",
        },
    )
    assert account.status_code == 201, account.text
    account_id = account.json()["id"]

    csv_content = (
        "Date,Description,Amount\n"
        "2024-03-01,Payroll ACME Corp,2500.00\n"
        "2024-03-02,Starbucks Coffee,-5.75\n"
        "2024-03-03,Transfer to Savings,-200.00\n"
        "2024-03-04,Local Grocery Market,-84.20\n"
    ).encode("utf-8")

    upload = client.post(
        "/api/v1/imports/upload",
        files={"file": ("statement.csv", BytesIO(csv_content), "text/csv")},
        data={"source_name": "Bank CSV", "financial_account_id": account_id},
    )
    assert upload.status_code == 200, upload.text
    import_id = upload.json()["import_id"]
    interpretation = upload.json()["interpretation"]
    assert interpretation["column_mappings"]
    assert interpretation["sample_normalized_rows"]

    preview = client.get(f"/api/v1/imports/interpretation?import_id={import_id}")
    assert preview.status_code == 200
    assert preview.json()["total"] >= 1

    correct = client.post(
        "/api/v1/imports/interpretation",
        json={
            "import_id": import_id,
            "corrections": {
                "amount_convention": "expenses_negative",
                "default_currency": "CAD",
            },
        },
    )
    assert correct.status_code == 200, correct.text

    confirm = client.post("/api/v1/imports/confirm", json={"import_id": import_id})
    assert confirm.status_code == 200, confirm.text
    summary = confirm.json()["summary"]
    assert summary["new_record_count"] == 4
    assert summary["failed_row_count"] == 0

    # Identical re-import should not create new events
    upload2 = client.post(
        "/api/v1/imports/upload",
        files={"file": ("statement-copy.csv", BytesIO(csv_content), "text/csv")},
        data={"source_name": "Bank CSV", "financial_account_id": account_id},
    )
    assert upload2.status_code == 200
    assert upload2.json()["identical_file_detected"] is True
    import_id2 = upload2.json()["import_id"]
    client.post(
        "/api/v1/imports/interpretation",
        json={"import_id": import_id2, "corrections": {}},
    )
    confirm2 = client.post("/api/v1/imports/confirm", json={"import_id": import_id2})
    assert confirm2.status_code == 200
    # Unchanged rows for same content identity path through normalize
    assert confirm2.json()["summary"]["new_record_count"] == 0
    assert confirm2.json()["summary"]["unchanged_record_count"] == 4

    tx = client.get("/api/v1/transactions")
    assert tx.status_code == 200
    items = tx.json()["items"]
    assert len(items) == 4
    assert any(i["overall_status"] for i in items)

    review = client.get("/api/v1/review")
    assert review.status_code == 200
    assert "stats" in review.json()

    dash = client.get("/api/v1/dashboard/summary")
    assert dash.status_code == 200
    body = dash.json()
    assert body["currency"] == "CAD"
    assert "monthly_income" in body
    assert "pending_expenses" in body

    cats = client.get("/api/v1/categories")
    names = {c["name"] for c in cats.json()["items"]}
    assert "Dining Out" in names
    assert "Healthcare" in names
    assert "Games" in names

    # Transfer should not inflate expenses as included spending incorrectly
    # (transfer analytics inclusion excluded when categorized as transfer)
    transfer = next(i for i in items if "transfer" in (i["original_description"] or "").lower())
    assert transfer["transaction_type"] == "transfer"
