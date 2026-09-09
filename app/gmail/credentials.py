import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from app.domain.errors import CredentialRefreshError, CredentialUnavailableError
SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

class CredentialProvider:
    def __init__(self, token_store, client_factory=Credentials.from_authorized_user_info): self.token_store, self.client_factory = token_store, client_factory
    def load(self, store_code):
        data = self.token_store.load(store_code)
        if not data: raise CredentialUnavailableError()
        try: creds = self.client_factory(data, SCOPES)
        except Exception as exc: raise CredentialUnavailableError() from exc
        if creds.valid: return creds
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request()); self.token_store.save(store_code, json.loads(creds.to_json())); return creds
            except Exception as exc: raise CredentialRefreshError() from exc
        raise CredentialUnavailableError()
