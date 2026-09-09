# Auto Email architecture

Auto Email is a deterministic scheduled Gmail draft-generation service for store operational reporting. Cloud Scheduler invokes an authenticated Cloud Run request; the application owns Gmail draft creation and Firestore run state. Neo AVO is not in the runtime path.

## Runtime and state

`POST /api/v1/runs/{store_code}` derives the business date in `Asia/Jakarta`, composes the fixed export-sales email, atomically acquires `auto_email_runs/{store}:export_sales:{date}`, creates one Gmail draft, and persists the confirmed draft ID. The logical document contains generation records with status (`RECEIVED`, `PROCESSING`, `COMPLETED`, `FAILED`, `EFFECT_UNCERTAIN`) and execution phase (`PRE_EFFECT`, `EFFECT_ATTEMPTED`, `EFFECT_CONFIRMED`). Firestore transactions ensure only one caller owns a generation.

Repeated scheduled delivery returns the completed draft. A correction requires `business_date` and a unique `correction_request_id`; it creates the next generation and records the superseded generation. Old Gmail drafts are not deleted.

## Boundaries and failure semantics

Domain composition and models are pure application concerns. Firestore and Gmail live behind infrastructure adapters. A confirmed Gmail draft is completed even if Telegram notification fails; Telegram is bounded and best-effort. A transport failure after a potentially-mutating Gmail call is `EFFECT_UNCERTAIN`, and normal retry refuses to create another draft. This cannot eliminate the external API's distributed-system ambiguity; operator reconciliation remains necessary.

Credentials are persisted authorized-user state, refreshed headlessly, and never recovered interactively in Cloud Run. `scripts/seed_token.py` is an explicit local operator tool only.

`/healthz` is liveness. `/readyz` reports configuration readiness without Gmail mutation or credential refresh. Production should use Cloud Run IAM/OIDC and `--no-allow-unauthenticated` for Scheduler invocation.

This service intentionally has no AI, frontend, generic workflow engine, worker, queue, or Neo AVO integration.
