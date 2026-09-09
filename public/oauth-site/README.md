# Auto Email OAuth Branding Site

This directory contains the minimal, dependency-free static website required for Google OAuth production branding and verification for **Auto Email**.

---

## 1. Production URLs

The site is designed to be hosted on your custom domain:

| Page | Production URL |
| :--- | :--- |
| **Home / Overview** | `https://auto-email.chaniago.me/` |
| **Privacy Policy** | `https://auto-email.chaniago.me/privacy` (or `/privacy.html`) |
| **Terms of Service** | `https://auto-email.chaniago.me/terms` (or `/terms.html`) |

---

## 2. Google OAuth Consent Screen Mapping

When configuring the **OAuth consent screen** in [Google Cloud Console](https://console.cloud.google.com/apis/credentials/consent):

| Google Cloud Console Field | Configured Value |
| :--- | :--- |
| **App name** | `Auto Email` |
| **User support email** | Your administrative email address |
| **Application home page** | `https://auto-email.chaniago.me/` |
| **Application privacy policy link** | `https://auto-email.chaniago.me/privacy` |
| **Application terms of service link** | `https://auto-email.chaniago.me/terms` |
| **Authorized domains** | `chaniago.me` |
| **Developer contact information** | Your administrative contact email |

---

## 3. Mandatory Domain Verification

Before Google Cloud Console accepts `chaniago.me` under **Authorized domains**, the domain must be verified:

1. Open [Google Search Console](https://search.google.com/search-console).
2. Add property `chaniago.me` (Domain or URL prefix).
3. Complete ownership verification (e.g. via DNS TXT record with your domain registrar/Cloudflare).
4. Ensure the Google account administering the GCP project is listed as a verified owner of the domain in Search Console.

---

## 4. Deployment Options

The site consists entirely of standalone HTML/CSS with zero dependencies or runtime processes.

### Option A: Cloudflare Pages (Recommended - Fastest & Free)
1. In Cloudflare Dashboard, navigate to **Compute (Workers) > Pages**.
2. Create an application pointing to your GitHub repository:
   - **Root directory:** `public/oauth-site`
   - **Build command:** *(leave empty)*
   - **Build output directory:** *(leave empty or `.`)*
3. Assign custom domain: `auto-email.chaniago.me`.
4. Enable standard clean URLs (Cloudflare automatically routes `/privacy` to `privacy.html`).

### Option B: Firebase Hosting (GCP Ecosystem Native)
If you prefer keeping everything in Google Cloud:
1. Initialize Firebase Hosting in a separate target or use `firebase.json`:
   ```json
   {
     "hosting": {
       "public": "public/oauth-site",
       "cleanUrls": true
     }
   }
   ```
2. Deploy: `firebase deploy --only hosting`.
3. Connect custom domain `auto-email.chaniago.me` via Firebase Console.

### Option C: GitHub Pages / Vercel
- Set root / publishing directory to `public/oauth-site`.
- Attach `auto-email.chaniago.me` CNAME record.
