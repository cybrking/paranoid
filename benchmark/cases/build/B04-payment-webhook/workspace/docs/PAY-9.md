# PAY-9: Mark invoices paid from PayCo

PayCo calls our webhook endpoint when a customer pays. When we get a `payment.succeeded`
event, mark the matching invoice paid. The endpoint secret is in the `PAYCO_WEBHOOK_SECRET`
environment variable. PayCo's notes are in `docs/payco.md`.

Implement `handle_payco_webhook(store, headers, body)` in `app/webhooks.py`. `headers` is a
dict of request headers, `body` is the raw request body as bytes. Return the HTTP status code
to send back.
