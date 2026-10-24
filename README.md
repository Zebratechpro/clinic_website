# Evergreen Family Clinic — Flask starter

A responsive clinic website built with Flask, SQLite, HTML, Tailwind CSS (CDN), and vanilla JavaScript.

## Included

- Responsive home/hero section, doctor profile, services, appointment form, contact details, footer and floating WhatsApp link
- English/Tamil language toggle with a remembered visitor preference
- SQLite persistence for appointment requests
- Server-side validation and protection against duplicate date/time slots
- Environment-based clinic details and WhatsApp configuration
- Appointment request emails to the clinic and styled receipt emails to patients who provide an email address
- Mobile navigation and accessible form labels
- Basic health-check endpoint at `/health`

## Run locally

Python 3.10+ recommended.

### 1. Create a virtual environment

**Windows PowerShell**
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install packages and configure

```bash
pip install -r requirements.txt
```

Configure the ignored `.env` file directly; it is intentionally excluded from Git and must not be committed. Set `APP_ENV=production`, generate a unique `SECRET_KEY` with `python -c "import secrets; print(secrets.token_hex(32))"`, and provide a unique admin username and password of at least 16 characters. For production, store this file only on the server with restricted permissions. The app defaults to production mode and refuses to start with missing or placeholder authentication settings. For local development only, set `APP_ENV=development` in `.env`; never use development mode in production. `WHATSAPP_NUMBER` must contain country code and digits only, without `+` or spaces (example format: `919876543210`).

### 3. Start the server

```bash
python app.py
```

Open http://127.0.0.1:5000

The SQLite database is created automatically on first run. Set `DATABASE_PATH` to choose another location.

## Customize before publishing

1. Replace **Evergreen Family Clinic**, Dr. `[Doctor Name]`, specialty, qualifications and experience with verified clinic information.
2. Replace the sample doctor photos with images the clinic owns or is licensed to use. Current images are loaded from Unsplash and require internet access.
3. Update phone, email, address, and WhatsApp number in `.env`.
4. For the embedded map, create a Google Maps embed URL and set `MAP_EMBED_URL` in `.env`. If omitted, the page shows a link to search the clinic address in Google Maps.
5. Update the service list and time slots to match the actual clinic schedule.

## Important production notes

- The form creates a **request**, not a confirmed booking. The clinic must contact the patient to confirm.
- The current database reserves each date/time slot globally. If the clinic has multiple doctors or multiple appointment capacity per slot, change the uniqueness rule and booking logic accordingly.
- Run behind a production WSGI server and an HTTPS-enforcing reverse proxy. Production session cookies are Secure, HttpOnly, and SameSite=Lax; HSTS and baseline security headers are set by the app. Keep TLS enabled at the proxy so browsers receive HSTS over HTTPS.
- Keep production secrets in the server's protected `.env` file, never commit it, and restrict file permissions. Rotate any SMTP app password previously present in the repository and update `MAIL_APP_PASSWORD` in `.env`.
- Configure rate limiting for login and appointment submissions at the HTTPS reverse proxy or WAF, and set up protected backups and monitoring before public deployment.
- Do not collect unnecessary medical information. Restrict database and server-log access, define retention/deletion rules, and comply with applicable privacy and healthcare requirements.
- Tailwind's CDN is convenient for development. For production, install Tailwind and compile a static CSS bundle.
- Run with `FLASK_DEBUG=false` in production; never expose Flask's development server to the public internet.
