from datetime import datetime, timezone
from app.config import Settings
from app.domain.email import compose_export_sales_email
from app.domain.errors import EffectUncertainError, UnsupportedStoreError
from app.domain.models import GenerationReason, RunIdentity, RunStatus
from app.domain.stores import get_store
from app.persistence.run_repository import InMemoryRunRepository
from app.service import AutoEmailService, business_date
from app.api.routes import create_app
from app.gmail.credentials import CredentialProvider
from app.domain.errors import CredentialRefreshError
from app.telemetry.neo_avo import NeoAvoTelemetry

class Drafts:
    def __init__(self, result='draft-1', error=None):
        self.calls = 0
        self.result = result
        self.error = error

    def create(self, store, email):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result

def settings():
    return Settings(
        project_id=None,
        email_recipients=('a@example.com',),
        firestore_database=None,
        neo_avo_base_url="https://neo-avo.chaniago.me",
        neo_avo_api_token="test-token",
        neo_avo_project_id="auto-email",
        neo_avo_environment="production",
    )

def test_jakarta_date_and_deterministic_composition():
    instant = datetime(2026, 9, 8, 17, 30, tzinfo=timezone.utc)
    assert business_date(instant).isoformat() == '2026-09-09'
    email = compose_export_sales_email(get_store('tp6'), business_date(instant), ('a@example.com',))
    assert email.subject == 'EXPORT SALES GC TP6 SURABAYA 9 SEPTEMBER 2026'
    assert email == compose_export_sales_email(get_store('tp6'), business_date(instant), ('a@example.com',))

def test_unsupported_store():
    try:
        get_store('x')
    except UnsupportedStoreError:
        pass
    else:
        assert False

def test_normal_duplicate_completed_and_concurrent_acquisition():
    repo = InMemoryRunRepository()
    drafts = Drafts()
    svc = AutoEmailService(settings(), repo, drafts)
    first = svc.run('tp6')
    second = svc.run('tp6')
    assert drafts.calls == 1 and second['draft_id'] == first['draft_id']
    identity = RunIdentity('pms', 'export_sales', business_date())
    a = repo.acquire(identity, GenerationReason.SCHEDULED)
    b = repo.acquire(identity, GenerationReason.SCHEDULED)
    assert a.acquired and not b.acquired

def test_correction_and_duplicate_request_are_idempotent():
    repo = InMemoryRunRepository()
    drafts = Drafts('draft-2')
    svc = AutoEmailService(settings(), repo, drafts)
    svc.run('tp6')
    correction = svc.run('tp6', business_date(), 'corr-1')
    duplicate = svc.run('tp6', business_date(), 'corr-1')
    assert correction['generation'] == 2 and duplicate['draft_id'] == 'draft-2' and drafts.calls == 2

def test_uncertain_is_not_retried():
    drafts = Drafts(error=EffectUncertainError())
    repo = InMemoryRunRepository()
    svc = AutoEmailService(settings(), repo, drafts)
    try:
        svc.run('tp6')
    except EffectUncertainError:
        pass
    else:
        assert False
    try:
        svc.run('tp6')
    except EffectUncertainError:
        pass
    else:
        assert False
    assert drafts.calls == 1 and repo.runs[next(iter(repo.runs))]['gens'][0].status == RunStatus.EFFECT_UNCERTAIN

def test_credential_refresh_failure_never_uses_interactive_oauth():
    class Creds:
        valid = False
        expired = True
        refresh_token = 'refresh'
        def refresh(self, request):
            raise RuntimeError('revoked secret')
        def to_json(self):
            return '{}'
    provider = CredentialProvider(type('Store', (), {'load': lambda self, code: {'token': 'x'}, 'save': lambda *args: None})(), lambda data, scopes: Creds())
    try:
        provider.load('tp6')
    except CredentialRefreshError:
        pass
    else:
        assert False

def test_health_and_safe_api_error():
    app = create_app(AutoEmailService(settings(), InMemoryRunRepository(), Drafts()), settings())
    client = app.test_client()
    assert client.get('/healthz').status_code == 200
    assert client.get('/readyz').status_code == 200
    response = client.post('/api/v1/runs/unknown')
    assert response.status_code == 400 and 'Unsupported store code' in response.json['error']['message'] and 'Traceback' not in response.text

def test_telemetry_success_and_failure_isolation():
    recorded = []
    class FakeResponse:
        status_code = 202
        text = '{"accepted":1}'
    def fake_sender(url, json=None, headers=None, timeout=None):
        recorded.append({"url": url, "json": json, "headers": headers})
        return FakeResponse()

    telemetry = NeoAvoTelemetry(api_token="test-tok", sender=fake_sender)
    svc = AutoEmailService(settings(), InMemoryRunRepository(), Drafts('draft-telemetry'), telemetry=telemetry)

    res = svc.run('tp6')
    assert res['status'] == 'success'
    assert res['draft_id'] == 'draft-telemetry'
    assert len(recorded) == 1

    event = recorded[0]["json"]["events"][0]
    assert event["schemaVersion"] == 1
    assert event["projectId"] == "auto-email"
    assert event["environment"] == "production"
    assert event["type"] == "task.completed"
    assert event["data"]["outcome"] == "created"
    assert event["data"]["draftId"] == "draft-telemetry"
    # Verify no sensitive info is emitted
    payload_str = str(recorded[0]["json"])
    assert "finance@indovaris.com" not in payload_str
    assert "token" not in event["data"]

    # Now verify telemetry failure does not alter business result
    def broken_sender(url, json=None, headers=None, timeout=None):
        raise TimeoutError("connection timeout to neo-avo")

    broken_telemetry = NeoAvoTelemetry(api_token="test-tok", sender=broken_sender)
    svc_broken = AutoEmailService(settings(), InMemoryRunRepository(), Drafts('draft-broken-telemetry'), telemetry=broken_telemetry)
    res2 = svc_broken.run('pms')
    assert res2['status'] == 'success'
    assert res2['draft_id'] == 'draft-broken-telemetry'

def test_telemetry_deterministic_event_id_and_replay():
    recorded = []
    class FakeResponse:
        status_code = 202
        text = '{"accepted":1}'
    def fake_sender(url, json=None, headers=None, timeout=None):
        recorded.append(json["events"][0])
        return FakeResponse()

    telemetry = NeoAvoTelemetry(api_token="test-tok", sender=fake_sender)
    repo = InMemoryRunRepository()
    svc = AutoEmailService(settings(), repo, Drafts('draft-rep'), telemetry=telemetry)

    svc.run('tp6')
    first_event = recorded[0]
    assert first_event["eventId"].endswith(":gen-1:completed")
    assert first_event["data"]["outcome"] == "created"

    # Replay
    svc.run('tp6')
    second_event = recorded[1]
    assert second_event["eventId"].endswith(":gen-1:replay")
    assert second_event["data"]["outcome"] == "idempotent_replay"
    assert first_event["eventId"] != second_event["eventId"]
