from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _get(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


def _get_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key, str(default)).lower()
    return val in ("true", "1", "yes")


# --- Mock flags ---
ALL_MOCK: bool = _get_bool("ALL_MOCK")

SHOPIFY_MOCK: bool = ALL_MOCK or _get_bool("SHOPIFY_MOCK")
GMAIL_MOCK: bool = ALL_MOCK or _get_bool("GMAIL_MOCK")
SHEETS_MOCK: bool = ALL_MOCK or _get_bool("SHEETS_MOCK")
SLACK_MOCK: bool = ALL_MOCK or _get_bool("SLACK_MOCK")

# --- Shopify ---
SHOPIFY_WEBHOOK_SECRET: str | None = _get("SHOPIFY_WEBHOOK_SECRET")

# --- Gmail ---
GMAIL_CREDENTIALS_PATH: str = _get("GMAIL_CREDENTIALS_PATH", "credentials.json")
GMAIL_TOKEN_PATH: str = _get("GMAIL_TOKEN_PATH", "token.json")
GMAIL_SENDER: str | None = _get("GMAIL_SENDER")

# --- Google Sheets ---
SHEETS_CREDENTIALS_PATH: str = _get("SHEETS_CREDENTIALS_PATH", "service_account.json")
SPREADSHEET_ID: str | None = _get("SPREADSHEET_ID")
SHEET_NAME: str = _get("SHEET_NAME", "Orders")

# --- Slack ---
SLACK_WEBHOOK_URL: str | None = _get("SLACK_WEBHOOK_URL")

# --- Server ---
PORT: int = int(_get("PORT", "8000"))
