# PayCo webhooks (vendor notes)

PayCo POSTs JSON events to your endpoint:

```json
{"id": "evt_123", "type": "payment.succeeded", "data": {"invoice_id": "inv_42", "amount_cents": 1200}}
```

Each request carries a `PayCo-Signature` header: `t=<unix seconds>,v1=<hex>`, where `v1` is
HMAC-SHA256 over `<t>.<raw body>` keyed with your endpoint secret. PayCo retries a delivery
for up to three days until it gets a 2xx response.
