import base64
from email.message import EmailMessage
from app.domain.errors import EffectUncertainError, GmailOperationError
class GmailDrafts:
    def __init__(self, client_factory): self.client_factory = client_factory
    def create(self, store_code, email):
        message = EmailMessage(); message['To'] = ', '.join(email.recipients); message['Subject'] = email.subject; message.set_content(email.body)
        body = {'message': {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}}
        try: result = self.client_factory.for_store(store_code).users().drafts().create(userId='me', body=body).execute()
        except (ConnectionError, TimeoutError) as exc: raise EffectUncertainError() from exc
        except Exception as exc: raise GmailOperationError() from exc
        if not isinstance(result, dict) or not result.get('id'): raise EffectUncertainError()
        return result['id']
