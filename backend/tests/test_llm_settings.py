"""Household LLM settings are stored encrypted and never returned in plaintext."""

from app.core.secrets import decrypt_secret, encrypt_secret, mask_secret


def test_encrypt_roundtrip():
    token = encrypt_secret("sk-test-secret-key")
    assert token != "sk-test-secret-key"
    assert decrypt_secret(token) == "sk-test-secret-key"


def test_mask_secret():
    assert mask_secret("sk-abcdefghij") == "sk-…ghij"


def test_save_llm_settings_masks_key(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "llmsettings@example.com",
            "password": "password123",
            "display_name": "Settings User",
        },
    )
    client.post(
        "/api/v1/auth/login",
        json={"email": "llmsettings@example.com", "password": "password123"},
    )
    client.post(
        "/api/v1/onboarding",
        json={
            "household_name": "LLM Household",
            "currency": "CAD",
            "timezone": "America/Toronto",
            "people": [{"name": "Person 1"}],
        },
    )

    saved = client.patch(
        "/api/v1/household-settings",
        json={
            "llm": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "api_key": "sk-live-should-not-echo",
            }
        },
    )
    assert saved.status_code == 200, saved.text
    body = saved.json()["settings"]["llm"]
    assert body["provider"] == "openai"
    assert body["has_api_key"] is True
    assert "sk-live" not in str(saved.json())
    assert "api_key_encrypted" not in str(saved.json())

    loaded = client.get("/api/v1/household-settings")
    assert loaded.status_code == 200
    assert loaded.json()["settings"]["llm"]["api_key_set"] is True
    assert "sk-live-should-not-echo" not in loaded.text
