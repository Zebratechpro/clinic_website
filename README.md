# Evergreen Family Clinic — Flask starter

A responsive clinic website built with Flask, SQLite, HTML, Tailwind CSS (CDN), and vanilla JavaScript.

## Included

- Responsive home/hero section, doctor profile, services, appointment form, contact details, footer and floating WhatsApp link
- SQLite persistence for appointment requests
- Server-side validation and protection against duplicate date/time slots
- Environment-based clinic details and WhatsApp configuration
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

Copy `.env.example` to `.env`, then update the clinic details. Use a long, random `SECRET_KEY` before deploying. `WHATSAPP_NUMBER` must contain country code and digits only, without `+` or spaces (example format: `919876543210`).

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
- Add CSRF protection (for example, Flask-WTF), rate limiting, HTTPS, secure cookie settings, backups, monitoring, and a proper production WSGI server before public deployment.
- Do not collect unnecessary medical information. Restrict database and server-log access, define retention/deletion rules, and comply with applicable privacy and healthcare requirements.
- Tailwind's CDN is convenient for development. For production, install Tailwind and compile a static CSS bundle.
- Run with `FLASK_DEBUG=false` in production; never expose Flask's development server to the public internet.
