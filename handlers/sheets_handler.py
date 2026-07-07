from __future__ import annotations

import logging
from datetime import datetime
from typing import List

import config
from models.order import Order

logger = logging.getLogger(__name__)

COLUMNS = ["Timestamp", "Order ID", "Customer", "Email", "Items", "Total", "Currency", "Status"]


def _build_row(order: Order) -> List[str]:
    return [
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        order.order_id,
        order.customer_name,
        order.customer_email,
        order.items_summary(),
        f"{order.total:.2f}",
        order.currency,
        "confirmed",
    ]


def _get_sheets_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = service_account.Credentials.from_service_account_file(
        config.SHEETS_CREDENTIALS_PATH, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def append_order(order: Order) -> None:
    row = _build_row(order)

    if config.SHEETS_MOCK:
        header = " | ".join(COLUMNS)
        values = " | ".join(row)
        print(f"\n[SHEETS MOCK] {header}")
        print(f"[SHEETS MOCK] {values}\n")
        logger.info("Sheets mock: row logged for order %s", order.order_id)
        return

    service = _get_sheets_service()
    body = {"values": [row]}
    service.spreadsheets().values().append(
        spreadsheetId=config.SPREADSHEET_ID,
        range=f"{config.SHEET_NAME}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()
    logger.info("Order %s appended to Google Sheet %s", order.order_id, config.SPREADSHEET_ID)
