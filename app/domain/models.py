from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
class RunStatus(str, Enum):
    RECEIVED='RECEIVED'; PROCESSING='PROCESSING'; COMPLETED='COMPLETED'; FAILED='FAILED'; EFFECT_UNCERTAIN='EFFECT_UNCERTAIN'
class ExecutionPhase(str, Enum):
    PRE_EFFECT='PRE_EFFECT'; EFFECT_ATTEMPTED='EFFECT_ATTEMPTED'; EFFECT_CONFIRMED='EFFECT_CONFIRMED'
class GenerationReason(str, Enum):
    SCHEDULED='SCHEDULED'; CORRECTION='CORRECTION'
@dataclass(frozen=True)
class RunIdentity:
    store_code: str; report_type: str; business_date: date
    @property
    def run_id(self): return f'{self.store_code}:{self.report_type}:{self.business_date.isoformat()}'
@dataclass
class Generation:
    generation: int; reason: GenerationReason; correction_request_id: str | None; status: RunStatus; execution_phase: ExecutionPhase
    draft_id: str | None = None; supersedes_generation: int | None = None; error_code: str | None = None; error_class: str | None = None
    started_at: datetime | None = None; completed_at: datetime | None = None
@dataclass(frozen=True)
class Acquisition:
    acquired: bool; generation: Generation | None = None; existing_draft_id: str | None = None; reason: str | None = None
