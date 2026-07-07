from __future__ import annotations

import hashlib
import hmac
import logging
import random
import string
from datetime import datetime
from typing import Any, Dict

import config
from models.order import Order, OrderItem

logger = logging.getLogger(__name__)

_MOCK_NAMES = ["Alice Johnson", "Bob Smith", "Clara Diaz", "David Kim", "Eva Nowak"]
_MOCK_PRODUCTS = [
    ("Wireless Headphones", 89.99),
    ("Mechanical Keyboard", 129.99),
    ("USB-C Hub", 39.99),
    ("Webcam 1080p", 59.99),
    ("Desk Lamp LED", 24.99),
    ("Mouse Pad XL", 19.99),
]


def _random_order_id() -> str:
    return "ORD-" + "".join(random.choices(string.digits, k=6))


def _generate_mock_order() -> Order:
    name = random.choice(_MOCK_NAMES)
    first = name.split()[0].lower()
    last = name.split()[1].lower()
    email = f"{first}.{last}@example.com"

    num_items = random.randint(1, 3)
    selected = random.sample(_MOCK_PRODUCTS, num_items)
    items = [
        OrderItem(name=p[0], qty=random.randint(1, 2), price=p[1])
        for p in selected
    ]
    total = round(sum(i.qty * i.price for i in items), 2)

    return Order(
        order_id=_random_order_id(),
        customer_name=name,
        customer_email=email,
        items=items,
        total=total,
        currency="USD",
        created_at=datetime.utcnow(),
    )


def verify_hmac(body: bytes, signature: str) -> bool:
    if not config.SHOPIFY_WEBHOOK_SECRET:
        logger.warning("SHOPIFY_WEBHOOK_SECRET not set — skipping HMAC verification")
        return True
    digest = hmac.new(
        config.SHOPIFY_WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, signature)


def parse_shopify_payload(payload: Dict[str, Any]) -> Order:
    line_items = payload.get("line_items", [])
    items = [
        OrderItem(
            name=item.get("title", "Unknown"),
            qty=int(item.get("quantity", 1)),
            price=float(item.get("price", 0)),
        )
        for item in line_items
    ]
    customer = payload.get("customer", {})
    first = customer.get("first_name", "")
    last = customer.get("last_name", "")
    email = payload.get("email", customer.get("email", "noreply@example.com"))

    return Order(
        order_id=str(payload.get("order_number", payload.get("id", "UNKNOWN"))),
        customer_name=f"{first} {last}".strip() or "Unknown Customer",
        customer_email=email,
        items=items,
        total=float(payload.get("total_price", 0)),
        currency=payload.get("currency", "USD"),
        created_at=datetime.utcnow(),
    )


def get_order(payload: Dict[str, Any] | None = None) -> Order:
    if config.SHOPIFY_MOCK:
        order = _generate_mock_order()
        logger.info("Mock order generated: %s", order.order_id)
        return order

    if payload is None:
        raise ValueError("Payload required when SHOPIFY_MOCK is disabled")

    order = parse_shopify_payload(payload)
    logger.info("Order parsed from Shopify payload: %s", order.order_id)
    return order
