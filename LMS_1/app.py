"""
Lead Management System — Flask App

How to run this project:

1. For development (on your computer):
   flask --app app run
   → Used for testing and building the app locally

2. For production (live server):
   gunicorn app:app
   → Used when deploying the app for real users on the internet
"""

from __future__ import annotations

import os
import re
# import smtplib
# from email.message import EmailMessage
from typing import Any
from flask import Flask, jsonify, render_template, request,session,redirect,url_for
from sqlalchemy import func, or_
from models import Lead, db



# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "leads.db")

app = Flask(__name__)
app.secret_key="secret123"

# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'pavanikaranam2002@gmail.com'
# app.config['MAIL_PASSWORD'] = 'xyqtylbdiyzfaozy'





# -----------------------------------------------------------------------------
# Validation helpers
# -----------------------------------------------------------------------------

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# E.164-style friendly: optional +, digits/spaces/dashes/parens; 10–15 digit characters
PHONE_REGEX = re.compile(r"^\+?[\d\s().-]{10,15}$")


def digits_only(phone: str) -> str:
    return re.sub(r"\D", "", phone)


def validate_phone(phone: str) -> bool:
    if not phone or not PHONE_REGEX.match(phone.strip()):
        return False
    count = len(digits_only(phone))
    return 10 <= count <= 15


def validate_lead_payload(data: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    """
    Validate required fields, email, and phone for create/update payloads.

    Returns (cleaned_fields_or_none, error_messages).
    """
    errors: list[str] = []
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    business_type = (data.get("business_type") or "").strip()
    message = (data.get("message") or "").strip()

    if not name:
        errors.append("Name is required.")
    if not email:
        errors.append("Email is required.")
    elif not EMAIL_REGEX.match(email):
        errors.append("Enter a valid email address.")
    if not phone:
        errors.append("Phone number is required.")
    elif not validate_phone(phone):
        errors.append(
            "Phone must be 10–15 digits; you may use spaces, dashes, or parentheses."
        )
    if not business_type:
        errors.append("Business type is required.")
    if not message:
        errors.append("Message is required.")

    if errors:
        return None, errors

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "business_type": business_type,
        "message": message,
    }, []


# -----------------------------------------------------------------------------
# Automatic reply + optional OpenAI placeholder
# -----------------------------------------------------------------------------


def build_auto_reply(name: str, business_type: str) -> str:
    """Generate a simple automatic acknowledgement (no external API)."""
    return (
        f"Hi {name}, thanks for reaching out about {business_type}. "
        "We have received your message and a member of our team will contact you shortly."
    )


def optional_openai_enhance_reply(base_reply: str, _context: dict[str, str]) -> str:
    """
      This is a placeholder for future OpenAI integration.

      If OpenAI is installed and OPENAI_API_KEY is set in environment variables,

      this function can be extended to generate AI-powered personalized replies.

      Currently, it returns the original automatic reply without modification

      so the application works without any external dependencies.
"""
    # Example future integration (commented — uncomment when ready):
    # import os
    # if os.environ.get("OPENAI_API_KEY"):  # "check if OpenAI API key is available in system environment"
    #    from openai import OpenAI
    #    client = OpenAI()
    #      This  is only initialization / preparation code...
    return base_reply


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        """Public lead submission page."""
        return render_template("index.html")

    @app.route("/dashboard")
    def dashboard():
        if "user" not in session:
            return redirect(url_for("login",
        next=request.path))
        """Admin-style lead list (same-origin; add auth in production)."""
        return render_template("dashboard.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        next_page = request.form.get("next") or request.args.get("next")

        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            if username == "admin" and password == "admin123":
                session["user"] = username
                return redirect(next_page or url_for("dashboard"))

            return render_template(
                "login.html",
                error="Invalid username or password",
                next=next_page
            )

        return render_template(
            "login.html",
            next=next_page
        )
    @app.route("/logout")
    def logout():

        session.pop("user", None)

        return redirect(url_for("login"))

    # --- REST API ---------------------------------------------------------

    @app.route("/api/leads", methods=["GET", "POST"])
    def api_leads():
        """
        GET:  list leads (?q= &status=)
        POST: create lead (JSON body)
        """
        if request.method == "POST":
            if not request.is_json:
                return jsonify({"ok": False, "errors": ["Expected JSON body."]}), 400
            data = request.get_json(silent=True) or {}
            cleaned, errors = validate_lead_payload(data)
            if errors:
                return jsonify({"ok": False, "errors": errors}), 400

            assert cleaned is not None
            #Duplicate email check
            existing_email = Lead.query.filter_by(
                email=cleaned["email"]
            ).first()
            if existing_email:

                return jsonify({
                    "ok":False,
                    "errors":["This email already exists"]

            }),400
            lead = Lead(
                name=cleaned["name"],
                email=cleaned["email"],
                phone=cleaned["phone"],
                business_type=cleaned["business_type"],
                message=cleaned["message"],
                status=Lead.STATUS_NEW,
            )
            db.session.add(lead)
            db.session.commit()

            # thank_you_subject = "Thank you for contacting us"
            # thank_you_body = (
            #     f"Dear {lead.name},\n\n"
            #     "Thank you for taking the time to share your inquiry with us. "
            #     "We have received your submission and appreciate your interest.\n\n"
            #     "A member of our team will review your message and follow up with you "
            #     "as soon as possible. If you have any additional details to share in the "
            #     "meantime, you may reply to this email.\n\n"
            #     "We look forward to speaking with you.\n\n"
            #     "Kind regards,\n"
            #     "The Team"
            # )
            # email_msg = EmailMessage()
            # email_msg["Subject"] = thank_you_subject
            # email_msg["From"] = app.config["MAIL_USERNAME"]
            # email_msg["To"] = lead.email
            # email_msg.set_content(thank_you_body)
            # try:
            #     with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            #         smtp.starttls()
            #         smtp.login(app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            #         smtp.send_message(email_msg)
            # except Exception as e:
            #     print(repr(e))

            base_reply = build_auto_reply(lead.name, lead.business_type)
            auto_reply = optional_openai_enhance_reply(
                base_reply,
                {
                    "name": lead.name,
                    "business_type": lead.business_type,
                    "message": lead.message,
                },
            )

            return (
                jsonify(
                    {
                        "ok": True,
                        "lead": lead.to_dict(),
                        "auto_reply": auto_reply,
                    }
                ),
                201,
            )

        # GET
        q = (request.args.get("q") or "").strip()
        status = (request.args.get("status") or "").strip()

        query = Lead.query.order_by(Lead.created_at.desc())  # Get all leads from DB

        if status:
            if status not in Lead.ALLOWED_STATUSES:
                return jsonify({"ok": False, "errors": [f"Invalid status: {status}"]}), 400
            query = query.filter(Lead.status == status)

        if q:
            # Portable case-insensitive search on SQLite
            like = f"%{q.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Lead.name).like(like),
                    func.lower(Lead.email).like(like),
                    func.lower(Lead.phone).like(like),
                    func.lower(Lead.business_type).like(like),
                    func.lower(Lead.message).like(like),
                )
            )

        leads = query.all()
        return jsonify({"ok": True, "leads": [lead.to_dict() for lead in leads]})

    @app.route("/api/leads/<int:lead_id>", methods=["PUT"])
    def api_update_lead(lead_id: int):
        """Update lead status (primary use case for the dashboard)."""
        if not request.is_json:
            return jsonify({"ok": False, "errors": ["Expected JSON body."]}), 400
        lead = db.session.get(Lead, lead_id)
        if lead is None:
            return jsonify({"ok": False, "errors": ["Lead not found."]}), 404

        data = request.get_json(silent=True) or {}
        new_status = (data.get("status") or "").strip()
        if not new_status:
            return jsonify({"ok": False, "errors": ["status is required."]}), 400
        if new_status not in Lead.ALLOWED_STATUSES:
            return jsonify(
                {
                    "ok": False,
                    "errors": [f"status must be one of: {', '.join(Lead.ALLOWED_STATUSES)}"],
                }
            ), 400

        lead.status = new_status
        db.session.commit()
        return jsonify({"ok": True, "lead": lead.to_dict()})


def create_app() -> Flask:
    """Application factory — keeps setup testable and Gunicorn-friendly."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-me-in-production")
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


app = create_app()
# Gunicorn: use `gunicorn app:app` (or `app:application` if your host expects that name).
application = app


# Local development server
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))