# Workspace Context: Gmail Draft Automation Service

Proyek ini adalah layanan serverless berbasis Python (Flask) yang dideploy ke **Google Cloud Run** dan dipicu secara berkala oleh **Cloud Scheduler** untuk membuat draft email otomatis di Gmail, serta mengirim laporan status sukses/gagal ke **Telegram Bot**.

---

## 1. Arsitektur & Alur Kerja
1. **Cloud Scheduler**: Mengirimkan HTTP POST ke endpoint `/jalankan-automasi` setiap hari pukul 08:00 WIB (atau sesuai konfigurasi cron).
2. **Cloud Run**: Menerima request HTTP POST, memvalidasi otorisasi OAuth2, membuat draft email baru melalui **Gmail API**.
3. **Telegram Bot**: Mengirimkan laporan instan berupa notifikasi berhasil atau detail error ke Telegram chat Anda.

---

## 2. Struktur Proyek
- `main.py`: Aplikasi utama menggunakan Flask dan Google Client Library.
- `requirements.txt`: Daftar pustaka dependensi Python.
- `Dockerfile`: File konfigurasi containerization untuk deployment GCP.
- `.gitignore`: Mengabaikan berkas kredensial (`token.json`, `credentials.json`, `.env`).

---

## 3. Environment Variables yang Dibutuhkan
Saat dideploy di Cloud Run (atau dijalankan lokal), pastikan env berikut telah diset:
- `TELEGRAM_BOT_TOKEN`: Token bot Telegram Anda.
- `TELEGRAM_CHAT_ID`: Chat ID Telegram Anda.
- `EMAIL_RECIPIENT`: Email penerima draft (Default: `tujuan@example.com`).
- `PORT`: Port aplikasi (Default: `8080`).

---

## 4. Langkah Persiapan & Pengembangan Selanjutnya
### A. Setup Google Cloud & API Credentials
1. Buka **Google Cloud Console**, buat proyek baru atau gunakan proyek yang ada.
2. Aktifkan **Gmail API** di proyek tersebut.
3. Konfigurasikan **OAuth Consent Screen** (pilih tipe *External* atau *Internal*, tambahkan email Anda sebagai *Test User*, dan tambahkan scope `https://www.googleapis.com/auth/gmail.compose`).
4. Buat **OAuth client ID** (Pilih tipe *Desktop Application*).
5. Unduh file kredensial JSON tersebut dan simpan di root proyek ini dengan nama **`credentials.json`**.

### B. Setup Lokal & First-Time Run
1. Jalankan aplikasi lokal terlebih dahulu untuk melakukan OAuth flow pertama kali (ini akan membuka browser untuk sign-in ke Google):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python main.py
   ```
2. Akses `/jalankan-automasi` via POST atau jalankan flow login untuk meng-generate file **`token.json`**. File ini berisi refresh token dan access token Gmail Anda.

### C. Deployment ke Google Cloud Run
Gunakan perintah berikut untuk mendeploy langsung menggunakan Dockerfile yang ada:
```bash
gcloud run deploy gmail-auto-draft \
  --source . \
  --platform managed \
  --region asia-southeast2 \
  --allow-unauthenticated \
  --set-env-vars TELEGRAM_BOT_TOKEN="TOKEN_BOT_ANDA",TELEGRAM_CHAT_ID="CHAT_ID_ANDA",EMAIL_RECIPIENT="EMAIL_TUJUAN"
```

### D. Setup Cloud Scheduler
Gunakan URL yang dihasilkan setelah deployment Cloud Run untuk memicu scheduler:
```bash
gcloud scheduler jobs create http trigger-draft-harian \
  --schedule="0 8 * * *" \
  --uri="https://URL_CLOUD_RUN_ANDA/jalankan-automasi" \
  --http-method=POST \
  --time-zone="Asia/Jakarta" \
  --location="asia-southeast2"
```
