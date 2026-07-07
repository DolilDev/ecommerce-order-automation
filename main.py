from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict

from flask import Flask, jsonify, request

import config
from handlers import gmail_handler, sheets_handler, slack_handler
from handlers.shopify_handler import get_order, verify_hmac

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def run_pipeline(payload: Dict[str, Any] | None) -> str:
    order = get_order(payload)
    logger.info("Processing order %s for %s", order.order_id, order.customer_name)

    tasks = {
        "gmail": lambda: gmail_handler.send_confirmation(order),
        "sheets": lambda: sheets_handler.append_order(order),
        "slack": lambda: slack_handler.send_notification(order),
    }

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fn): name for name, fn in tasks.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                future.result()
                logger.info("Handler '%s' completed successfully", name)
            except Exception as exc:
                logger.error("Handler '%s' failed: %s", name, exc)
                raise RuntimeError(f"Handler '{name}' failed: {exc}") from exc

    logger.info("Pipeline completed for order %s", order.order_id)
    return order.order_id


@app.route("/webhook/order", methods=["POST"])
def webhook_order():
    body = request.get_data()
    signature = request.headers.get("X-Shopify-Hmac-Sha256", "")

    if not config.SHOPIFY_MOCK and not verify_hmac(body, signature):
        logger.warning("Invalid HMAC signature — request rejected")
        return jsonify({"status": "error", "detail": "invalid signature"}), 401

    payload = request.get_json(silent=True)

    try:
        order_id = run_pipeline(payload)
        return jsonify({"status": "ok", "order_id": order_id}), 200
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        return jsonify({"status": "error", "detail": str(exc)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, debug=False)
