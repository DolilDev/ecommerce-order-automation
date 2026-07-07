# ecommerce-order-automation

A Python webhook server that listens for Shopify orders and automatically sends email confirmations via Gmail, logs each order to Google Sheets, and posts a summary to Slack — all triggered by a single HTTP request.

---

## Architecture

```
POST /webhook/order
        │
        ▼
┌───────────────────┐
│   Flask server    │  validates payload / generates mock order
│   (main.py)       │
└────────┬──────────┘
         │ Order object
         ▼
┌────────────────────────────────────────────┐
│              Pipeline (ThreadPoolExecutor) │
│                                            │
│  ┌─────────────┐  ┌──────────────────┐    │
│  │ gmail       │  │ sheets           │    │
│  │ send HTML   │  │ append row       │    │
│  │ confirmation│  │ to spreadsheet   │    │
│  └─────────────┘  └──────────────────┘    │
│                                            │
│  ┌─────────────┐                           │
│  │ slack       │                           │
│  │ Block Kit   │                           │
│  │ notification│                           │
│  └─────────────┘                           │
└────────────────────────────────────────────┘
         │
         ▼
  {"status": "ok", "order_id": "ORD-XXXXXX"}
```

---

## Tech stack

| Technology | Purpose |
|---|---|
| Flask 3.x | Webhook server |
| Pydantic v2 | Order model validation |
| google-api-python-client | Gmail and Sheets API |
| gspread | Google Sheets helper |
| requests | Slack Incoming Webhook |
| python-dotenv | Environment variable loading |
| pytest | Tests |

---

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/DolilDev/ecommerce-order-automation.git
   cd ecommerce-order-automation
   ```

2. Create and activate a virtual environment:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the env example and configure:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your credentials (or leave `ALL_MOCK=true` for local testing).

---

## Running in mock mode

Set `ALL_MOCK=true` in `.env` to run the full pipeline without any real API credentials. All handlers print their output to the console instead of calling external services.

Start the server:
```bash
ALL_MOCK=true python main.py
```

Trigger the webhook:
```bash
curl -X POST http://localhost:8000/webhook/order \
  -H "Content-Type: application/json" \
  -d '{}'
```

Expected response:
```json
{"order_id": "ORD-482931", "status": "ok"}
```

---

## Connecting real APIs

### Shopify
Generate a webhook in your Shopify admin under **Settings → Notifications → Webhooks**. Set the topic to `orders/create` and point the URL to your server. Copy the signing secret to `SHOPIFY_WEBHOOK_SECRET` in `.env`.
Docs: https://shopify.dev/docs/apps/webhooks/configuration/https#step-5-verify-the-webhook

### Gmail
Create an OAuth 2.0 credential in Google Cloud Console with the Gmail API enabled. Download `credentials.json` and place it in the project root. On first run with `GMAIL_MOCK=false`, a browser window opens for authorization and `token.json` is saved automatically.
Docs: https://developers.google.com/gmail/api/quickstart/python

### Google Sheets
Create a service account in Google Cloud Console with the Sheets API enabled. Download the key as `service_account.json`. Share your target spreadsheet with the service account email. Set `SPREADSHEET_ID` to the ID from the sheet URL.
Docs: https://developers.google.com/sheets/api/guides/authorizing

### Slack
Create a Slack app at https://api.slack.com/apps, enable Incoming Webhooks, and add a webhook to your target channel. Paste the webhook URL into `SLACK_WEBHOOK_URL` in `.env`.
Docs: https://api.slack.com/messaging/webhooks

---

## Running tests

```bash
pytest tests/
```

All tests run in mock mode automatically. Expected output: 5 passed.

---

## Project structure

```
ecommerce-order-automation/
├── main.py                       # Flask server, pipeline orchestration
├── config.py                     # Env vars and mock flags
├── handlers/
│   ├── shopify_handler.py        # Webhook parsing and mock order generation
│   ├── gmail_handler.py          # HTML confirmation email via Gmail API
│   ├── sheets_handler.py         # Row append via Google Sheets API
│   └── slack_handler.py          # Block Kit notification via Slack webhook
├── models/
│   └── order.py                  # Order and OrderItem Pydantic models
├── tests/
│   └── test_pipeline.py          # Pytest tests for pipeline and models
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```
