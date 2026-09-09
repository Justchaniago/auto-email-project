from __future__ import annotations
from dataclasses import dataclass
import os
from app.domain.stores import STORE_CONFIGS

@dataclass(frozen=True)
class Settings:
    project_id: str | None
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    email_recipients: tuple[str, ...]
    firestore_database: str | None
    telegram_timeout_seconds: float = 3.0

    @classmethod
    def from_env(cls):
        raw = os.getenv('EMAIL_RECIPIENT', 'finance@indovaris.com, andyal@indovaris.com')
        recipients = tuple(x.strip() for x in raw.replace(';', ',').split(',') if x.strip())
        return cls(os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT'), os.getenv('TELEGRAM_BOT_TOKEN'), os.getenv('TELEGRAM_CHAT_ID'), recipients, os.getenv('FIRESTORE_DATABASE_ID'))

    def validate(self):
        return ['EMAIL_RECIPIENT is empty'] if not self.email_recipients else []
