from dataclasses import dataclass
from datetime import date
from app.domain.stores import Store

MONTHS_ID = ('JANUARI', 'FEBRUARI', 'MARET', 'APRIL', 'MEI', 'JUNI', 'JULI', 'AGUSTUS', 'SEPTEMBER', 'OKTOBER', 'NOVEMBER', 'DESEMBER')
@dataclass(frozen=True)
class ComposedEmail:
    recipients: tuple[str, ...]
    subject: str
    body: str

def compose_export_sales_email(store: Store, business_date: date, recipients: tuple[str, ...]):
    date_str = f'{business_date.day} {MONTHS_ID[business_date.month - 1]} {business_date.year}'
    subject = f'EXPORT SALES {store.display_name} SURABAYA {date_str}'
    body = (f'Selamat Siang Team Finance,\n\nBerikut saya lampirkan data export sales {store.display_name} '
            f'tanggal {date_str} Mohon untuk di cek kembali.\n\nThank you and regard\n{store.signoff}')
    return ComposedEmail(recipients, subject, body)
