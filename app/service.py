from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from app.domain.email import compose_export_sales_email
from app.domain.errors import EffectUncertainError, RunConflictError
from app.domain.models import GenerationReason, RunIdentity
from app.domain.stores import get_store
JAKARTA = ZoneInfo('Asia/Jakarta')
def business_date(now=None): return (now or datetime.now(timezone.utc)).astimezone(JAKARTA).date()
class AutoEmailService:
    def __init__(self, settings, repository, drafts, notifier): self.settings,self.repository,self.drafts,self.notifier=settings,repository,drafts,notifier
    def run(self, store_code, date_value=None, correction_request_id=None):
        store=get_store(store_code); correction=correction_request_id is not None
        if correction and not correction_request_id.strip(): raise ValueError('correction_request_id required')
        identity=RunIdentity(store.code,'export_sales',date_value or business_date()); reason=GenerationReason.CORRECTION if correction else GenerationReason.SCHEDULED
        acquisition=self.repository.acquire(identity,reason,correction_request_id)
        if not acquisition.acquired:
            if acquisition.existing_draft_id: return {'status':'success','draft_id':acquisition.existing_draft_id,'generation':acquisition.generation.generation if acquisition.generation else None,'idempotent':True}
            if acquisition.reason=='effect_uncertain': raise EffectUncertainError()
            raise RunConflictError()
        gen=acquisition.generation
        try: draft_id=self.drafts.create(store.code,compose_export_sales_email(store,identity.business_date,self.settings.email_recipients))
        except EffectUncertainError as exc:
            self.repository.fail(identity,gen.generation,exc,uncertain=True)
            try: self.notifier.notify(f'[{store.display_name}] Gmail effect uncertain',{'event':'gmail_effect_uncertain','store_code':store.code})
            except Exception: pass
            raise
        except Exception as exc:
            self.repository.fail(identity,gen.generation,exc)
            try: self.notifier.notify(f'[{store.display_name}] Gmail draft failed',{'event':'gmail_draft_failed','store_code':store.code})
            except Exception: pass
            raise
        self.repository.complete(identity,gen.generation,draft_id)
        try: self.notifier.notify(f'[{store.display_name}] Gmail Draft Created: {draft_id}',{'event':'gmail_draft_created','store_code':store.code})
        except Exception: pass
        return {'status':'success','draft_id':draft_id,'generation':gen.generation,'business_date':identity.business_date.isoformat()}
