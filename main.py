import os
import base64
from email.message import EmailMessage
from flask import Flask, request, jsonify
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)

# Scopes required for Gmail Compose
SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

def get_gmail_service(store_code):
    creds = None
    token_file = f'token_{store_code}.json'
    
    # Check if specific token file exists
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    # If credentials not valid, let user log in or refresh
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                send_telegram_notification(f"⚠️ [{store_code.upper()}] Error refreshing token: {str(e)}")
                creds = None
        
        if not creds:
            # Fallback to local authentication (credentials.json must exist)
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("credentials.json not found. Place it in the root directory.")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save credentials for specific store
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
            
    return build('gmail', 'v1', credentials=creds)

def send_telegram_notification(message):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not bot_token or not chat_id:
        print("Telegram configuration missing.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

@app.route('/jalankan-automasi/<store_code>', methods=['POST'])
def run_automation(store_code):
    store_code = store_code.lower()
    if store_code not in ['tp6', 'pms']:
        return jsonify({"status": "error", "message": "Invalid store code. Use 'tp6' or 'pms'."}), 400

    # Map store code to display name
    store_names = {
        'tp6': 'GC TP6',
        'pms': 'GC PMS'
    }
    store_display = store_names[store_code]

    try:
        service = get_gmail_service(store_code)
        
        # Get current date in Indonesian format (e.g. 4 AGUSTUS 2026)
        import datetime
        
        MONTHS_ID = {
            1: "JANUARI", 2: "FEBRUARI", 3: "MARET", 4: "APRIL",
            5: "MEI", 6: "JUNI", 7: "JULI", 8: "AGUSTUS",
            9: "SEPTEMBER", 10: "OKTOBER", 11: "NOVEMBER", 12: "DESEMBER"
        }
        
        now = datetime.datetime.now()
        date_str = f"{now.day} {MONTHS_ID[now.month]} {now.year}"
        
        # Get multiple recipients from env or default to target indovaris emails
        recipient_env = os.environ.get('EMAIL_RECIPIENT', 'finance@indovaris.com, andyal@indovaris.com')
        # Replace semicolons with commas to avoid gcloud deploy syntax issues
        recipient_env = recipient_env.replace(';', ',')
        recipients = [r.strip() for r in recipient_env.split(',') if r.strip()]
        
        # Build email
        message = EmailMessage()
        message['To'] = ", ".join(recipients)
        message['Subject'] = f"EXPORT SALES {store_display} SURABAYA {date_str}"
        
        email_body = (
            f"Selamat Siang Team Finance,\n\n"
            f"Berikut saya lampirkan data export sales {store_display} tanggal {date_str} "
            f"Mohon untuk di cek kembali.\n\n"
            f"Thank you and regard\n"
            f"GCTP"
        )
        message.set_content(email_body)
        
        # Encode message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_draft_body = {
            'message': {
                'raw': encoded_message
            }
        }
        
        # Create draft via Gmail API
        draft = service.users().drafts().create(userId="me", body=create_draft_body).execute()
        
        success_msg = f"✅ *[{store_display}] Gmail Draft Created!*\nDraft ID: `{draft['id']}`\nTo: {', '.join(recipients)}"
        send_telegram_notification(success_msg)
        return jsonify({"status": "success", "draft_id": draft['id']}), 200

    except Exception as e:
        error_msg = f"❌ *[{store_display}] Gmail Draft Failed!*\nError: `{str(e)}`"
        send_telegram_notification(error_msg)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    # Cloud Run binds to PORT environment variable
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
