from datetime import datetime, timezone
from threading import RLock
from google.cloud import firestore
from app.domain.models import Acquisition, ExecutionPhase, Generation, GenerationReason, RunStatus

class InMemoryRunRepository:
    def __init__(self): self.runs, self._lock = {}, RLock()
    def acquire(self, identity, reason, correction_request_id=None):
        with self._lock:
            run = self.runs.setdefault(identity.run_id, {'gens': []})
            for gen in run['gens']:
                if correction_request_id and gen.correction_request_id == correction_request_id: return Acquisition(False, gen, gen.draft_id, 'duplicate_correction')
            if reason == GenerationReason.SCHEDULED:
                for gen in run['gens']:
                    if gen.status == RunStatus.COMPLETED: return Acquisition(False, gen, gen.draft_id, 'completed')
                if any(gen.status == RunStatus.PROCESSING for gen in run['gens']): return Acquisition(False, reason='processing')
                if any(gen.status == RunStatus.EFFECT_UNCERTAIN for gen in run['gens']): return Acquisition(False, reason='effect_uncertain')
            n = len(run['gens']) + 1; now = datetime.now(timezone.utc)
            gen = Generation(n, reason, correction_request_id, RunStatus.PROCESSING, ExecutionPhase.PRE_EFFECT, started_at=now, supersedes_generation=n-1 if reason == GenerationReason.CORRECTION else None)
            run['gens'].append(gen); return Acquisition(True, gen)
    def complete(self, identity, generation, draft_id):
        with self._lock:
            gen = self.runs[identity.run_id]['gens'][generation-1]; gen.draft_id=draft_id; gen.status=RunStatus.COMPLETED; gen.execution_phase=ExecutionPhase.EFFECT_CONFIRMED; gen.completed_at=datetime.now(timezone.utc)
    def fail(self, identity, generation, error, uncertain=False):
        with self._lock:
            gen = self.runs[identity.run_id]['gens'][generation-1]; gen.status=RunStatus.EFFECT_UNCERTAIN if uncertain else RunStatus.FAILED; gen.execution_phase=ExecutionPhase.EFFECT_ATTEMPTED if uncertain else ExecutionPhase.PRE_EFFECT; gen.error_code=error.code; gen.error_class=error.__class__.__name__

class FirestoreRunRepository:
    """The transaction claims one logical generation; only its owner may call Gmail."""
    def __init__(self, db): self.db = db
    def acquire(self, identity, reason, correction_request_id=None):
        ref = self.db.collection('auto_email_runs').document(identity.run_id)
        @firestore.transactional
        def txn(transaction):
            snap = ref.get(transaction=transaction); data = snap.to_dict() if snap.exists else {'store_code':identity.store_code,'report_type':identity.report_type,'business_date':identity.business_date.isoformat(),'generations':[]}
            gens = data.get('generations', [])
            for item in gens:
                if correction_request_id and item.get('correction_request_id') == correction_request_id: return Acquisition(False, existing_draft_id=item.get('draft_id'), reason='duplicate_correction')
            if reason == GenerationReason.SCHEDULED:
                done = next((x for x in gens if x.get('status') == RunStatus.COMPLETED.value), None)
                if done: return Acquisition(False, existing_draft_id=done.get('draft_id'), reason='completed')
                if any(x.get('status') in (RunStatus.PROCESSING.value, RunStatus.EFFECT_UNCERTAIN.value) for x in gens): return Acquisition(False, reason='processing')
            n=len(gens)+1; now=datetime.now(timezone.utc); item={'generation':n,'reason':reason.value,'correction_request_id':correction_request_id,'status':RunStatus.PROCESSING.value,'execution_phase':ExecutionPhase.PRE_EFFECT.value,'started_at':now,'supersedes_generation':n-1 if reason == GenerationReason.CORRECTION else None}; gens.append(item); data.update(generations=gens,current_generation=n,updated_at=now,created_at=data.get('created_at',now)); transaction.set(ref,data)
            return Acquisition(True, Generation(n,reason,correction_request_id,RunStatus.PROCESSING,ExecutionPhase.PRE_EFFECT,started_at=now,supersedes_generation=n-1 if reason == GenerationReason.CORRECTION else None))
        return txn(self.db.transaction())
    def _update(self, identity, generation, **changes):
        ref=self.db.collection('auto_email_runs').document(identity.run_id)
        @firestore.transactional
        def txn(transaction):
            snap=ref.get(transaction=transaction); data=snap.to_dict(); data['generations'][generation-1].update(changes); data['updated_at']=datetime.now(timezone.utc); transaction.set(ref,data)
        txn(self.db.transaction())
    def complete(self, identity, generation, draft_id): self._update(identity,generation,draft_id=draft_id,status=RunStatus.COMPLETED.value,execution_phase=ExecutionPhase.EFFECT_CONFIRMED.value,completed_at=datetime.now(timezone.utc))
    def fail(self, identity, generation, error, uncertain=False): self._update(identity,generation,status=(RunStatus.EFFECT_UNCERTAIN if uncertain else RunStatus.FAILED).value,execution_phase=(ExecutionPhase.EFFECT_ATTEMPTED if uncertain else ExecutionPhase.PRE_EFFECT).value,error_code=error.code,error_class=error.__class__.__name__)
