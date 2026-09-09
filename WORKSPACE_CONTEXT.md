# Auto Email workspace

This repository contains the Auto Email modular monolith: a deterministic Cloud Run service invoked by Cloud Scheduler to generate Gmail drafts for TP6 and PMS operational reporting. Firestore owns durable run state and idempotency; Telegram is best-effort notification only.

See `README.md` for local validation, `ARCHITECTURE.md` for boundaries and failure semantics, and `NEO_AVO_INTEGRATION.md` for the intentionally deferred telemetry boundary.
