import os
import base64
import datetime
from flask import Flask, jsonify
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "TOKEN_BOT_TELEGRAM_ANDA")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "CHAT_ID_TELEGRAM_ANDA")
SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

def kirim_notifikasi_telegram(pesan):
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "TOKEN_BOT_TELEGRAM_ANDA":
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": pesan,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Gagal kirim telegram: {e}")

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

@app.route('/jalankan-automasi', methods=['POST'])
def endpoint_scheduler():
    try:
        service = get_gmail_service()
        email_penerima = os.environ.get("EMAIL_RECIPIENT", "tujuan@example.com")
        tanggal_hari_ini = datetime.date.today().strftime('%d %B %Y')
        subjek_email = f"Laporan Harian Otomatis - {tanggal_hari_ini}"
        
        body_template = (
            f"Halo,\n\n"
            f"Berikut adalah draf laporan harian otomatis untuk tanggal {tanggal_hari_ini}.\n"
            f"Sistem berjalan dengan lancar tanpa hambatan.\n\n"
            f"Salam,\nAsisten Otomasi Cloud Run"
        )
        
        message = MIMEText(body_template)
        message['to'] = email_penerima
        message['subject'] = subjek_email
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        draft_body = {'message': {'raw': raw_message}}
        
        draft = service.users().drafts().create(userId='me', body=draft_body).execute()
        
        notif_text = f"✅ *Sukses Automasi Draft!*\nDraft email ke `{email_penerima}` dengan subjek *{subjek_email}* telah berhasil dibuat di Gmail Anda."
        kirim_notifikasi_telegram(notif_text)
        
        return jsonify({"status": "success", "draft_id": draft['id']}), 200

    except Exception as error:
        err_msg = f"❌ *Gagal membuat draft email otomatis:*\n`{str(error)}`"
        kirim_notifikasi_telegram(err_msg)
        return jsonify({"status": "error", "message": str(error)}), 500

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "service": "Gmail Automation Service"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
