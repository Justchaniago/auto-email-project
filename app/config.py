from __future__ import annotations
from dataclasses import dataclass
import os
from app.domain.stores import STORE_CONFIGS

@dataclass(frozen=True)
class Settings:
    project_id: str | None
    email_recipients: tuple[str, ...]
    firestore_database: str | None = None
    neo_avo_base_url: str = "https://neo-avo.chaniago.me"
    neo_avo_api_token: str | None = None
    neo_avo_project_id: str = "auto-email"
    neo_avo_environment: str = "production"
    neo_avo_timeout_seconds: float = 3.0

    @classmethod
    def from_env(cls) -> Settings:
        raw = os.getenv('EMAIL_RECIPIENT', 'finance@indovaris.com, andyal@indovaris.com')
        recipients = tuple(x.strip() for x in raw.replace(';', ',').split(',') if x.strip())
        return cls(
            project_id=os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT'),
            email_recipients=recipients,
            firestore_database=os.getenv('FIRESTORE_DATABASE_ID'),
            neo_avo_base_url=os.getenv('NEO_AVO_BASE_URL', 'https://neo-avo.chaniago.me'),
            neo_avo_api_token=os.getenv('NEO_AVO_API_TOKEN'),
            neo_avo_project_id=os.getenv('NEO_AVO_PROJECT_ID', 'auto-email'),
            neo_avo_environment=os.getenv('NEO_AVO_ENVIRONMENT', 'production'),
            neo_avo_timeout_seconds=float(os.getenv('NEO_AVO_TIMEOUT_SECONDS', '3.0')),
        )

    def validate(self) -> list[str]:
        return ['EMAIL_RECIPIENT is empty'] if not self.email_recipients else []
