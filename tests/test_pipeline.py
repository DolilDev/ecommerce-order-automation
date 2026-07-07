from __future__ import annotations

import json
import os
import pytest

os.environ["ALL_MOCK"] = "true"

from datetime import datetime

from models.order import Order, OrderItem


# --- Order model tests ---

def test_order_model_valid():
    order = Order(
        order_id="ORD-001",
        customer_name="Jane Doe",
        customer_email="jane@example.com",
        items=[OrderItem(name="Keyboard", qty=1, price=99.99)],
        total=99.99,
        currency="USD",
        created_at=datetime.utcnow(),
    )
    assert order.order_id == "ORD-001"
    assert order.total == 99.99
    assert order.items_summary() == "1x Keyboard"


def test_order_model_empty_items_raises():
    with pytest.raises(Exception):
        Order(
            order_id="ORD-002",
            customer_name="John Doe",
            customer_email="john@example.com",
            items=[],
            total=0.0,
            currency="USD",
            created_at=datetime.utcnow(),
        )


def test_order_item_negative_qty_raises():
    with pytest.raises(Exception):
        OrderItem(name="Mouse", qty=-1, price=29.99)


# --- Slack payload structure test ---

def test_slack_payload_structure():
    from handlers.slack_handler import _build_payload

    order = Order(
        order_id="ORD-TEST",
        customer_name="Test User",
        customer_email="test@example.com",
        items=[OrderItem(name="Monitor", qty=1, price=299.99)],
        total=299.99,
        currency="USD",
        created_at=datetime.utcnow(),
    )
    payload = _build_payload(order)

    assert "blocks" in payload
    assert len(payload["blocks"]) >= 3
    header = payload["blocks"][0]
    assert header["type"] == "header"
    assert "ORD-TEST" in header["text"]["text"]


# --- Webhook endpoint test ---

def test_webhook_endpoint_returns_ok():
    from main import app

    app.config["TESTING"] = True
    client = app.test_client()

    response = client.post(
        "/webhook/order",
        data=json.dumps({}),
        content_type="application/json",
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert "order_id" in data
    assert data["order_id"].startswith("ORD-")


def test_health_endpoint():
    from main import app

    app.config["TESTING"] = True
    client = app.test_client()

    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
