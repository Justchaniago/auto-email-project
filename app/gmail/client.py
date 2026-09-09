from googleapiclient.discovery import build
class GmailClientFactory:
    def __init__(self, credentials): self.credentials = credentials
    def for_store(self, store_code): return build('gmail', 'v1', credentials=self.credentials.load(store_code), cache_discovery=False)
