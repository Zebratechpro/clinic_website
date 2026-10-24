import os
import re
import smtplib
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps
from pathlib import Path
from urllib.parse import urlencode

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "clinic.db"))
APP_ENV = os.getenv("APP_ENV", "production").strip().lower()
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

if APP_ENV not in {"development", "production"}:
    raise ValueError("APP_ENV must be either 'development' or 'production'.")
if len(SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY must be configured with at least 32 characters.")
if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise ValueError("ADMIN_USERNAME and ADMIN_PASSWORD must be configured.")
if APP_ENV == "production":
    if SECRET_KEY.lower().startswith(("replace-", "change-", "dev-")):
        raise ValueError("Set SECRET_KEY to a unique, randomly generated production secret.")
    if ADMIN_USERNAME.lower() in {"admin", "change_me", "replace_me"} or any(
        marker in ADMIN_USERNAME.lower() for marker in ("replace", "change")
    ):
        raise ValueError("Set ADMIN_USERNAME to a unique production username.")
    if len(ADMIN_PASSWORD) < 16 or ADMIN_PASSWORD.lower() in {"admin123", "password"} or any(
        marker in ADMIN_PASSWORD.lower() for marker in ("replace", "change")
    ):
        raise ValueError("ADMIN_PASSWORD must be a unique production password of at least 16 characters.")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=APP_ENV == "production",
)
csrf = CSRFProtect(app)
MAIL_TO = os.getenv("MAIL_TO", "zenovahcc@gmail.com")
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_TO)
MAIL_HOST = os.getenv("MAIL_HOST", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_USERNAME = os.getenv("MAIL_USERNAME", MAIL_TO)
MAIL_APP_PASSWORD = os.getenv("MAIL_APP_PASSWORD", "").strip()
CLINIC_ADDRESS = os.getenv(
    "CLINIC_ADDRESS",
    "242/5i1, MRN Nagar, Durgam Road, Kallakurichi - 606202",
)


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if APP_ENV == "production":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
    return response


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    return "Form validation failed. Reload the page and try again.", 400


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                service TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                message TEXT,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(appointment_date, appointment_time)
            )
        """)


def send_appointment_email(appointment):
    if not MAIL_APP_PASSWORD:
        app.logger.warning("MAIL_APP_PASSWORD is not configured; skipping appointment email send.")
        return False

    subject = f"New appointment request: {appointment['patient_name']}"
    body = """\
New appointment request received.

Patient: {patient_name}
Phone: {phone}
Email: {email}
Service: {service}
Date: {appointment_date}
Time: {appointment_time}
Message: {message}
""".format(
        patient_name=appointment["patient_name"],
        phone=appointment["phone"],
        email=appointment["email"] or "Not provided",
        service=appointment["service"],
        appointment_date=appointment["appointment_date"],
        appointment_time=appointment["appointment_time"],
        message=appointment["message"] or "No extra notes",
    )

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = MAIL_FROM
    message["To"] = MAIL_TO

    try:
        with smtplib.SMTP(MAIL_HOST, MAIL_PORT) as smtp:
            smtp.starttls()
            smtp.login(MAIL_USERNAME, MAIL_APP_PASSWORD)
            smtp.sendmail(MAIL_FROM, [MAIL_TO], message.as_string())
        return True
    except Exception:
        app.logger.exception("Failed to send appointment email")
        return False


def send_patient_appointment_email(appointment):
    if not appointment["email"]:
        return False
    if not MAIL_APP_PASSWORD:
        app.logger.warning("MAIL_APP_PASSWORD is not configured; skipping patient confirmation email.")
        return False

    appointment_date = datetime.strptime(
        appointment["appointment_date"], "%Y-%m-%d"
    ).strftime("%A, %B %d, %Y")
    appointment_time = datetime.strptime(
        appointment["appointment_time"], "%H:%M"
    ).strftime("%I:%M %p").lstrip("0")
    location_url = "https://www.google.com/maps/search/?" + urlencode({
        "api": "1",
        "query": f"Zenova Health Care Centre & Clinic, {CLINIC_ADDRESS}",
    })
    email_message = MIMEMultipart("alternative")
    email_message["Subject"] = "We received your appointment request | Zenova"
    email_message["From"] = MAIL_FROM
    email_message["To"] = appointment["email"]

    text_body = f"""\
Hello {appointment['patient_name']},

Thank you for contacting Zenova Health Care Centre & Clinic. We have received your appointment request.

REQUEST DETAILS
Service: {appointment['service']}
Preferred date: {appointment_date}
Preferred time: {appointment_time}

This is a request receipt, not a confirmed appointment. Our clinic team will contact you to confirm availability.

Need help? Call {os.getenv('CLINIC_PHONE', '+91 9994044418')} or email {os.getenv('CLINIC_EMAIL', 'zenovahcc@gmail.com')}.

Zenova Health Care Centre & Clinic
{CLINIC_ADDRESS}
View clinic location: {location_url}
"""
    html_body = render_template(
        "emails/appointment_confirmation.html",
        patient_name=appointment["patient_name"],
        service=appointment["service"],
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        clinic_phone=os.getenv("CLINIC_PHONE", "+91 9994044418"),
        clinic_email=os.getenv("CLINIC_EMAIL", "zenovahcc@gmail.com"),
        clinic_address=CLINIC_ADDRESS,
        location_url=location_url,
    )
    email_message.attach(MIMEText(text_body, "plain", "utf-8"))
    email_message.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(MAIL_HOST, MAIL_PORT) as smtp:
            smtp.starttls()
            smtp.login(MAIL_USERNAME, MAIL_APP_PASSWORD)
            smtp.sendmail(MAIL_FROM, [appointment["email"]], email_message.as_string())
        return True
    except Exception:
        app.logger.exception("Failed to send patient appointment confirmation email")
        return False


def admin_login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped_view


@app.get("/")
def home():
    return render_template(
        "index.html",
        today=date.today().isoformat(),
        whatsapp_number=os.getenv("WHATSAPP_NUMBER", "9994044418"),
        clinic_phone=os.getenv("CLINIC_PHONE", "+91 9994044418"),
        clinic_email=os.getenv("CLINIC_EMAIL", "hello@exampleclinic.com"),
        clinic_address=os.getenv("CLINIC_ADDRESS", "123 Main Road, Your City, India"),
        map_embed_url=os.getenv("MAP_EMBED_URL", ""),
    )


@app.post("/book-appointment")
def book_appointment():
    name = request.form.get("patient_name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    service = request.form.get("service", "").strip()
    appointment_date = request.form.get("appointment_date", "").strip()
    appointment_time = request.form.get("appointment_time", "").strip()
    message = request.form.get("message", "").strip()

    allowed_services = {
        "Hypertension management", "Diabetes management", "Diabetes wound care",
        "Thyroid treatment", "Weight management", "Lab diagnostics", "Home visits",
        "Home care", "Hairfall treatment", "Skin care", "General Consultation",
        "Home Check-up", "Follow-up Visit", "Preventive Care", "Other"
    }
    allowed_times = {
        "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
        "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"
    }

    if not name or len(name) > 100:
        flash("Please enter your name (up to 100 characters).", "error")
        return redirect(url_for("home") + "#appointment")
    if not re.fullmatch(r"[0-9+\s().-]{7,20}", phone):
        flash("Please enter a valid phone number.", "error")
        return redirect(url_for("home") + "#appointment")
    if email and (len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)):
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("home") + "#appointment")
    if service not in allowed_services:
        flash("Please select a valid appointment type.", "error")
        return redirect(url_for("home") + "#appointment")
    try:
        chosen_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
    except ValueError:
        chosen_date = None
    if not chosen_date or chosen_date < date.today():
        flash("Choose today or a future date.", "error")
        return redirect(url_for("home") + "#appointment")
    if appointment_time not in allowed_times:
        flash("Please select one of the available time slots.", "error")
        return redirect(url_for("home") + "#appointment")
    if len(message) > 1000:
        flash("Your message must be 1,000 characters or fewer.", "error")
        return redirect(url_for("home") + "#appointment")

    appointment = {
        "patient_name": name,
        "phone": phone,
        "email": email or None,
        "service": service,
        "appointment_date": appointment_date,
        "appointment_time": appointment_time,
        "message": message or None,
    }

    try:
        with get_db() as conn:
            cursor = conn.execute(
                """
                    INSERT INTO appointments
                    (patient_name, phone, email, service, appointment_date, appointment_time, message)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    appointment["patient_name"],
                    appointment["phone"],
                    appointment["email"],
                    appointment["service"],
                    appointment["appointment_date"],
                    appointment["appointment_time"],
                    appointment["message"],
                ),
            )
            appointment["id"] = cursor.lastrowid

        send_appointment_email(appointment)
        send_patient_appointment_email(appointment)
        flash("Your appointment request has been received. The clinic will contact you to confirm.", "success")
    except sqlite3.IntegrityError:
        flash("That time slot has just been requested. Please choose another time.", "error")
    except sqlite3.Error:
        app.logger.exception("Could not save appointment")
        flash("We couldn't save your request right now. Please contact the clinic by phone or WhatsApp.", "error")

    return redirect(url_for("home") + "#appointment")


@app.get("/admin")
@admin_login_required
def admin_dashboard():
    with get_db() as conn:
        appointments = conn.execute(
            "SELECT * FROM appointments ORDER BY created_at DESC"
        ).fetchall()

    return render_template("admin_dashboard.html", appointments=appointments)


@app.get("/admin/login")
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_login.html")


@app.post("/admin/login")
def admin_login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session["admin_logged_in"] = True
        session["admin_username"] = username
        flash("Login successful.", "success")
        return redirect(url_for("admin_dashboard"))

    flash("Invalid username or password.", "error")
    return redirect(url_for("admin_login"))


@app.post("/admin/logout")
def admin_logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("admin_login"))


@app.get("/health")
def health():
    return {"status": "ok"}


init_db()

if __name__ == "__main__":
    debug_enabled = APP_ENV == "development" and os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_enabled)
