# Auto Email workspace

This repository contains the Auto Email modular monolith: a deterministic Cloud Run service invoked by Cloud Scheduler to generate Gmail drafts for TP6 and PMS operational reporting. Firestore owns durable run state and idempotency. Auto Email's core operation is strictly Gmail draft creation. Operational observability and notifications are owned externally by Neo AVO.

See `README.md` for local validation, `ARCHITECTURE.md` for boundaries and failure semantics, and `NEO_AVO_INTEGRATION.md` for the intentionally deferred telemetry boundary.
