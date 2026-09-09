# Neo AVO integration preparation

Neo AVO is deliberately not integrated in this pass. The future boundary is a best-effort, bounded HTTP `POST /api/v1/events` using a dedicated Auto Email project credential. Telemetry must never be required for Gmail success, idempotency, or request completion.

Suggested identity: `projectId=auto-email`, `environment=production`. Candidate events include run received/processing/completed/failed/effect_uncertain, Gmail draft created/credential failed/refresh failed, Telegram delivery failed, scheduler trigger rejected, and correction requested/completed.

Safe metadata is limited to store, report type, business date, generation, reason, duration, execution phase, and status. Never send email content, recipients, OAuth or Telegram secrets, token state, raw Gmail payloads, or secret values. Do not use Cloud Logging routing, Pub/Sub, or Firestore reads as the integration mechanism.
