import logging
import requests
log = logging.getLogger(__name__)
class TelegramNotifier:
    def __init__(self, token, chat_id, timeout=3.0, sender=requests.post): self.token,self.chat_id,self.timeout,self.sender=token,chat_id,timeout,sender
    def notify(self, message, context=None):
        if not self.token or not self.chat_id: return False
        try:
            response=self.sender(f'https://api.telegram.org/bot{self.token}/sendMessage',json={'chat_id':self.chat_id,'text':message},timeout=self.timeout); response.raise_for_status(); return True
        except Exception: log.warning('telegram_delivery_failed',extra={'event':'telegram_delivery_failed',**(context or {})}); return False
