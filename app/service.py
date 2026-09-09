from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from app.domain.email import compose_export_sales_email
from app.domain.errors import EffectUncertainError, RunConflictError
from app.domain.models import GenerationReason, RunIdentity
from app.domain.stores import get_store
from app.telemetry.neo_avo import NoOpTelemetry

JAKARTA = ZoneInfo('Asia/Jakarta')

def business_date(now=None):
    return (now or datetime.now(timezone.utc)).astimezone(JAKARTA).date()

class AutoEmailService:
    def __init__(self, settings, repository, drafts, telemetry=None):
        self.settings = settings
        self.repository = repository
        self.drafts = drafts
        self.telemetry = telemetry or NoOpTelemetry()

    def run(self, store_code, date_value=None, correction_request_id=None):
        store = get_store(store_code)
        correction = correction_request_id is not None
        if correction and not correction_request_id.strip():
            raise ValueError('correction_request_id required')
        identity = RunIdentity(store.code, 'export_sales', date_value or business_date())
        reason = GenerationReason.CORRECTION if correction else GenerationReason.SCHEDULED
        acquisition = self.repository.acquire(identity, reason, correction_request_id)
        if not acquisition.acquired:
            if acquisition.existing_draft_id:
                gen_num = acquisition.generation.generation if acquisition.generation else 1
                self.telemetry.emit_run_completed(
                    store_code=store.code,
                    business_date=identity.business_date,
                    generation=gen_num,
                    generation_reason=reason.value,
                    draft_id=acquisition.existing_draft_id,
                    is_replay=True,
                )
                return {
                    'status': 'success',
                    'draft_id': acquisition.existing_draft_id,
                    'generation': acquisition.generation.generation if acquisition.generation else None,
                    'idempotent': True
                }
            if acquisition.reason == 'effect_uncertain':
                gen_num = acquisition.generation.generation if acquisition.generation else 1
                self.telemetry.emit_run_effect_uncertain(
                    store_code=store.code,
                    business_date=identity.business_date,
                    generation=gen_num,
                    generation_reason=reason.value,
                    error_code="EFFECT_UNCERTAIN",
                    error_message="Previous execution effect uncertain; replay refused",
                )
                raise EffectUncertainError()
            gen_num = acquisition.generation.generation if acquisition.generation else 1
            self.telemetry.emit_run_failed(
                store_code=store.code,
                business_date=identity.business_date,
                generation=gen_num,
                generation_reason=reason.value,
                error_code="RUN_CONFLICT",
                error_message="Concurrent execution conflict",
            )
            raise RunConflictError()
        gen = acquisition.generation
        try:
            draft_id = self.drafts.create(
                store.code,
                compose_export_sales_email(store, identity.business_date, self.settings.email_recipients)
            )
        except EffectUncertainError as exc:
            self.repository.fail(identity, gen.generation, exc, uncertain=True)
            self.telemetry.emit_run_effect_uncertain(
                store_code=store.code,
                business_date=identity.business_date,
                generation=gen.generation,
                generation_reason=reason.value,
                error_code="EFFECT_UNCERTAIN",
                error_message="Gmail draft mutation effect uncertain",
            )
            raise
        except Exception as exc:
            self.repository.fail(identity, gen.generation, exc)
            self.telemetry.emit_run_failed(
                store_code=store.code,
                business_date=identity.business_date,
                generation=gen.generation,
                generation_reason=reason.value,
                error_code=exc.__class__.__name__,
                error_message=str(exc),
            )
            raise
        self.repository.complete(identity, gen.generation, draft_id)
        self.telemetry.emit_run_completed(
            store_code=store.code,
            business_date=identity.business_date,
            generation=gen.generation,
            generation_reason=reason.value,
            draft_id=draft_id,
            is_replay=False,
        )
        return {
            'status': 'success',
            'draft_id': draft_id,
            'generation': gen.generation,
            'business_date': identity.business_date.isoformat()
        }
