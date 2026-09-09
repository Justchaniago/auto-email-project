from dataclasses import dataclass
from app.domain.errors import UnsupportedStoreError

@dataclass(frozen=True)
class Store:
    code: str
    display_name: str
    signoff: str

# GCTP is retained for both stores pending a confirmed PMS business sign-off.
STORE_CONFIGS = {'tp6': Store('tp6', 'GC TP6', 'GCTP'), 'pms': Store('pms', 'GC PMS', 'GCTP')}

def get_store(code):
    try: return STORE_CONFIGS[code.lower()]
    except KeyError as exc: raise UnsupportedStoreError() from exc
