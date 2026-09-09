from google.cloud import firestore
def create_client(project_id=None, database=None):
    kwargs = {}
    if project_id: kwargs['project'] = project_id
    if database: kwargs['database'] = database
    return firestore.Client(**kwargs)
class FirestoreTokenStore:
    def __init__(self, db): self.db = db
    def load(self, store_code):
        snap = self.db.collection('gmail_tokens').document(store_code).get(); return snap.to_dict() if snap.exists else None
    def save(self, store_code, token_data): self.db.collection('gmail_tokens').document(store_code).set(token_data)
