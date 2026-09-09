from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Any
import requests

log = logging.getLogger(__name__)

class NoOpTelemetry:
    def emit_run_completed(self, *args: Any, **kwargs: Any) -> None:
        pass

    def emit_run_failed(self, *args: Any, **kwargs: Any) -> None:
        pass

    def emit_run_effect_uncertain(self, *args: Any, **kwargs: Any) -> None:
        pass

class NeoAvoTelemetry:
    def __init__(
        self,
        base_url: str = "https://neo-avo.chaniago.me",
        api_token: str | None = None,
        project_id: str = "auto-email",
        environment: str = "production",
        timeout_seconds: float = 3.0,
        sender: Any = requests.post,
    ):
        self.base_url = (base_url or "").rstrip("/")
        self.api_token = api_token
        self.project_id = project_id
        self.environment = environment
        self.timeout_seconds = timeout_seconds
        self.sender = sender

    def emit_run_completed(
        self,
        store_code: str,
        business_date: Any,
        generation: int,
        generation_reason: str,
        draft_id: str | None,
        is_replay: bool,
    ) -> None:
        try:
            outcome = "idempotent_replay" if is_replay else "created"
            semantic = "replay" if is_replay else "completed"
            event_id = self._build_event_id(store_code, business_date, generation, semantic)
            task_id = self._build_task_id(store_code, business_date, generation)

            data = {
                "taskId": task_id,
                "taskType": "export_sales_draft",
                "store": store_code,
                "businessDate": business_date.isoformat() if hasattr(business_date, "isoformat") else str(business_date),
                "generation": generation,
                "generationReason": generation_reason,
                "outcome": outcome,
                "draftId": draft_id,
                "status": "COMPLETED",
            }
            self._dispatch("task.completed", event_id, data)
        except Exception as exc:
            log.warning("neo_avo_emit_run_completed_suppressed", extra={"error": str(exc)})

    def emit_run_failed(
        self,
        store_code: str,
        business_date: Any,
        generation: int,
        generation_reason: str,
        error_code: str,
        error_message: str,
    ) -> None:
        try:
            event_id = self._build_event_id(store_code, business_date, generation, "failed")
            task_id = self._build_task_id(store_code, business_date, generation)

            data = {
                "taskId": task_id,
                "taskType": "export_sales_draft",
                "store": store_code,
                "businessDate": business_date.isoformat() if hasattr(business_date, "isoformat") else str(business_date),
                "generation": generation,
                "generationReason": generation_reason,
                "outcome": "failed",
                "errorCode": str(error_code)[:160],
                "error": str(error_message)[:200],
                "status": "FAILED",
            }
            self._dispatch("task.failed", event_id, data)
        except Exception as exc:
            log.warning("neo_avo_emit_run_failed_suppressed", extra={"error": str(exc)})

    def emit_run_effect_uncertain(
        self,
        store_code: str,
        business_date: Any,
        generation: int,
        generation_reason: str,
        error_code: str = "EFFECT_UNCERTAIN",
        error_message: str = "Gmail draft mutation effect uncertain",
    ) -> None:
        try:
            event_id = self._build_event_id(store_code, business_date, generation, "effect_uncertain")
            task_id = self._build_task_id(store_code, business_date, generation)

            data = {
                "taskId": task_id,
                "taskType": "export_sales_draft",
                "store": store_code,
                "businessDate": business_date.isoformat() if hasattr(business_date, "isoformat") else str(business_date),
                "generation": generation,
                "generationReason": generation_reason,
                "outcome": "effect_uncertain",
                "errorCode": str(error_code)[:160],
                "error": str(error_message)[:200],
                "status": "EFFECT_UNCERTAIN",
            }
            self._dispatch("task.failed", event_id, data)
        except Exception as exc:
            log.warning("neo_avo_emit_run_effect_uncertain_suppressed", extra={"error": str(exc)})

    def _build_event_id(self, store_code: str, business_date: Any, generation: int, semantic: str) -> str:
        date_str = business_date.isoformat() if hasattr(business_date, "isoformat") else str(business_date)
        return f"evt:auto-email:{self.environment}:{store_code}:export_sales:{date_str}:gen-{generation}:{semantic}"

    def _build_task_id(self, store_code: str, business_date: Any, generation: int) -> str:
        date_str = business_date.isoformat() if hasattr(business_date, "isoformat") else str(business_date)
        return f"auto-email:{store_code}:export_sales:{date_str}:gen-{generation}"

    def _dispatch(self, event_type: str, event_id: str, data: dict[str, Any]) -> None:
        if not self.api_token or not self.base_url:
            log.debug("neo_avo_telemetry_skipped_no_token", extra={"event_id": event_id})
            return

        occurred_at = datetime.now(timezone.utc).isoformat()
        payload = {
            "events": [
                {
                    "schemaVersion": 1,
                    "eventId": event_id,
                    "projectId": self.project_id,
                    "environment": self.environment,
                    "type": event_type,
                    "occurredAt": occurred_at,
                    "data": data,
                }
            ]
        }
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "X-Neo-Avo-Environment": self.environment,
            "Content-Type": "application/json",
        }

        try:
            url = f"{self.base_url}/api/v1/events"
            resp = self.sender(url, json=payload, headers=headers, timeout=self.timeout_seconds)
            if resp.status_code not in (200, 201, 202):
                log.warning(
                    "neo_avo_telemetry_rejected",
                    extra={
                        "event_id": event_id,
                        "status_code": resp.status_code,
                        "response_text": resp.text[:200],
                    },
                )
            else:
                log.info("neo_avo_telemetry_emitted", extra={"event_id": event_id, "event_type": event_type})
        except Exception as exc:
            log.warning(
                "neo_avo_telemetry_delivery_failed",
                extra={"event_id": event_id, "error": str(exc)},
            )
