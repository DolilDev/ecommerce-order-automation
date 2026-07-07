from __future__ import annotations

import base64
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config
from models.order import Order

logger = logging.getLogger(__name__)


def _build_html(order: Order) -> str:
    rows = "".join(
        f"<tr>"
        f"<td style='padding:6px 12px;border-bottom:1px solid #eee'>{item.name}</td>"
        f"<td style='padding:6px 12px;border-bottom:1px solid #eee;text-align:center'>{item.qty}</td>"
        f"<td style='padding:6px 12px;border-bottom:1px solid #eee;text-align:right'>${item.price:.2f}</td>"
        f"<td style='padding:6px 12px;border-bottom:1px solid #eee;text-align:right'>${item.qty * item.price:.2f}</td>"
        f"</tr>"
        for item in order.items
    )
    return f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333">
  <h2 style="color:#1a1a1a">Order #{order.order_id} confirmed</h2>
  <p>Hi {order.customer_name},</p>
  <p>Thank you for your order. We are now processing it and will notify you once it ships.</p>

  <table style="width:100%;border-collapse:collapse;margin:20px 0">
    <thead>
      <tr style="background:#f5f5f5">
        <th style="padding:8px 12px;text-align:left">Product</th>
        <th style="padding:8px 12px;text-align:center">Qty</th>
        <th style="padding:8px 12px;text-align:right">Unit price</th>
        <th style="padding:8px 12px;text-align:right">Subtotal</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
    <tfoot>
      <tr>
        <td colspan="3" style="padding:10px 12px;text-align:right;font-weight:bold">Total</td>
        <td style="padding:10px 12px;text-align:right;font-weight:bold">${order.total:.2f} {order.currency}</td>
      </tr>
    </tfoot>
  </table>

  <p style="color:#666;font-size:13px">Your order is being processed. You will receive a shipping confirmation shortly.</p>
  <p style="color:#999;font-size:12px">Order placed: {order.created_at.strftime('%Y-%m-%d %H:%M UTC')}</p>
</body>
</html>
"""


def _get_gmail_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    import os

    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    creds = None

    if os.path.exists(config.GMAIL_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(config.GMAIL_TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.GMAIL_CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(config.GMAIL_TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def send_confirmation(order: Order) -> None:
    subject = f"Order #{order.order_id} confirmed — thank you, {order.customer_name}!"
    html_body = _build_html(order)

    if config.GMAIL_MOCK:
        print(f"\n[GMAIL MOCK] To: {order.customer_email}")
        print(f"[GMAIL MOCK] Subject: {subject}")
        print(f"[GMAIL MOCK] Body (HTML):\n{html_body}\n")
        logger.info("Gmail mock: confirmation logged for order %s", order.order_id)
        return

    service = _get_gmail_service()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.GMAIL_SENDER
    msg["To"] = order.customer_email
    msg.attach(MIMEText(html_body, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    logger.info("Confirmation email sent to %s for order %s", order.customer_email, order.order_id)
