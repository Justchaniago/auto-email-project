# Neo AVO Integration

Auto Email delivers best-effort operational telemetry to Neo AVO via `POST https://neo-avo.chaniago.me/api/v1/events`.

## Architecture & Failure Isolation Invariant

- Auto Email owns scheduler-triggered Gmail draft creation and Firestore run state.
- Neo AVO is strictly an external observer and owns centralized monitoring and alerts.
- Telemetry is dispatched best-effort. If Neo AVO is unavailable, slow, timing out, or returning errors, Auto Email's core business execution continues unimpeded.
- Telemetry failure never alters, retries, rolls back, or duplicates Gmail draft mutations.
- No direct Telegram integration exists in Auto Email.

## Ingestion Contract

- **Endpoint**: `POST https://neo-avo.chaniago.me/api/v1/events`
- **Headers**:
  - `Authorization: Bearer <NEO_AVO_API_TOKEN>`
  - `X-Neo-Avo-Environment: production`
  - `Content-Type: application/json`
- **Payload Schema**: Canonical envelope `{"events": [ ... ]}` with `schemaVersion: 1`.
- **Event Types**:
  - `task.completed`: Emitted on successful scheduled creation and idempotent replay.
  - `task.failed`: Emitted on deterministic failure, `EFFECT_UNCERTAIN`, or execution conflicts.
- **Deterministic Event ID Pattern**:
  `evt:auto-email:<env>:<store>:export_sales:<YYYY-MM-DD>:gen-<generation>:<outcome>`
  Ensures exact deduplication in Neo AVO (`ON CONFLICT (event_id) DO NOTHING`).
- **Data Privacy**:
  Only operational metadata (`taskId`, `taskType`, `store`, `businessDate`, `generation`, `generationReason`, `outcome`, `draftId`, `status`, sanitized `errorCode`) is transmitted. Secrets, OAuth tokens, email bodies, and report data are never sent.

## GCP Production Configuration

- **Secret Manager**: `neo-avo-auto-email-api-token` in `auto-email-production`
- **Environment Variable**: `NEO_AVO_API_TOKEN` bound to the secret in Cloud Run
