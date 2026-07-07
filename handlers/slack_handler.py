from __future__ import annotations

import json
import logging
from typing import Any, Dict

import requests

import config
from models.order import Order

logger = logging.getLogger(__name__)


def _build_payload(order: Order) -> Dict[str, Any]:
    item_count = sum(i.qty for i in order.items)
    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f":shopping_cart: New order confirmed — #{order.order_id}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Customer:*\n{order.customer_name}"},
                    {"type": "mrkdwn", "text": f"*Email:*\n{order.customer_email}"},
                    {"type": "mrkdwn", "text": f"*Total:*\n${order.total:.2f} {order.currency}"},
                    {"type": "mrkdwn", "text": f"*Items:*\n{item_count} item(s)"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Order summary:*\n{order.items_summary()}",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Placed at {order.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
                    }
                ],
            },
            {"type": "divider"},
        ]
    }


def send_notification(order: Order) -> None:
    payload = _build_payload(order)

    if config.SLACK_MOCK:
        print(f"\n[SLACK MOCK] Payload:\n{json.dumps(payload, indent=2)}\n")
        logger.info("Slack mock: notification logged for order %s", order.order_id)
        return

    if not config.SLACK_WEBHOOK_URL:
        raise ValueError("SLACK_WEBHOOK_URL is not set")

    response = requests.post(
        config.SLACK_WEBHOOK_URL,
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    logger.info("Slack notification sent for order %s", order.order_id)
