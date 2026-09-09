import logging
from datetime import date
from flask import Flask, jsonify, request
from app.config import Settings
from app.domain.errors import AutoEmailError
from app.gmail.client import GmailClientFactory
from app.gmail.credentials import CredentialProvider
from app.gmail.drafts import GmailDrafts
from app.persistence.firestore import FirestoreTokenStore, create_client
from app.persistence.run_repository import FirestoreRunRepository
from app.service import AutoEmailService
from app.telemetry.neo_avo import NeoAvoTelemetry

log = logging.getLogger(__name__)

def create_app(service=None, settings=None):
    app = Flask(__name__)
    settings = settings or Settings.from_env()
    if service is None:
        db = create_client(settings.project_id, settings.firestore_database)
        creds = CredentialProvider(FirestoreTokenStore(db))
        telemetry = NeoAvoTelemetry(
            base_url=settings.neo_avo_base_url,
            api_token=settings.neo_avo_api_token,
            project_id=settings.neo_avo_project_id,
            environment=settings.neo_avo_environment,
            timeout_seconds=settings.neo_avo_timeout_seconds,
        )
        service = AutoEmailService(
            settings,
            FirestoreRunRepository(db),
            GmailDrafts(GmailClientFactory(creds)),
            telemetry=telemetry,
        )

    @app.errorhandler(AutoEmailError)
    def known_error(error):
        return jsonify({'status': 'error', 'error': {'code': error.code, 'message': error.safe_message}}), error.http_status

    @app.errorhandler(Exception)
    def unknown_error(error):
        log.exception('unhandled_request_error', extra={'event': 'unhandled_request_error'})
        return jsonify({'status': 'error', 'error': {'code': 'internal_error', 'message': 'The request could not be completed.'}}), 500

    @app.get('/healthz')
    def healthz():
        return jsonify({'status': 'live'}), 200

    @app.get('/readyz')
    def readyz():
        errors = settings.validate()
        return (jsonify({'status': 'not_ready', 'checks': {'configuration': 'failed'}}), 503) if errors else (jsonify({'status': 'ready', 'checks': {'configuration': 'ok', 'persistence': 'deferred_until_request'}}), 200)

    def execute(store_code, correction=False):
        payload = request.get_json(silent=True) or {}
        date_value = None
        if correction:
            try:
                date_value = date.fromisoformat(payload['business_date'])
            except (KeyError, TypeError, ValueError):
                return jsonify({'status': 'error', 'error': {'code': 'invalid_business_date', 'message': 'business_date must be YYYY-MM-DD.'}}), 400
            if not isinstance(payload.get('correction_request_id'), str) or not payload['correction_request_id'].strip():
                return jsonify({'status': 'error', 'error': {'code': 'correction_request_id_required', 'message': 'correction_request_id is required.'}}), 400
        return jsonify(service.run(store_code, date_value, payload.get('correction_request_id') if correction else None)), 200

    app.add_url_rule('/api/v1/runs/<store_code>', 'normal_run', execute, methods=['POST'])
    app.add_url_rule('/api/v1/runs/<store_code>/corrections', 'correction_run', lambda store_code: execute(store_code, True), methods=['POST'])
    return app
