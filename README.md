# Auto Email

Deterministic scheduled Gmail draft-generation service for store operational reporting. It supports `tp6` and `pms`, derives business dates in `Asia/Jakarta`, and uses Firestore as the durable idempotency ledger.

## Local validation

```bash
python -m pytest -q
```

The production image runs Gunicorn and does not include `credentials.json`. Gmail runtime credentials must be authorized token state in Firestore. Use `python -m scripts.seed_token <store_code>` locally for the one-time browser authorization, then upload the resulting token through an explicit operator procedure.

## API

- `POST /api/v1/runs/tp6` or `/pms`: normal scheduled run; the date is derived in Jakarta.
- `POST /api/v1/runs/{store}/corrections`: requires JSON `{ "business_date": "YYYY-MM-DD", "correction_request_id": "unique-id" }`.
- `GET /healthz`: liveness.
- `GET /readyz`: configuration readiness.

Deployments are intentionally not performed by this repository pass. Production Cloud Run should require IAM/OIDC Scheduler invocation (`--no-allow-unauthenticated`). See [ARCHITECTURE.md](ARCHITECTURE.md) and [NEO_AVO_INTEGRATION.md](NEO_AVO_INTEGRATION.md).
