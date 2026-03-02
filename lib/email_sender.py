import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st


def _get_secret(key: str) -> str:
    try:
        return st.secrets[key]
    except Exception:
        return os.environ[key]


def _send(to_email: str, subject: str, body: str):
    sender = _get_secret("GMAIL_SENDER")
    password = _get_secret("GMAIL_APP_PASSWORD")

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, to_email, msg.as_string())


# ── Templates ──────────────────────────────────────────────────────────────────

def hired_template(first_name: str, role_name: str) -> tuple[str, str]:
    subject = f"Congratulations! You've been selected for {role_name}"
    body = f"""Hi {first_name},

We are thrilled to inform you that after careful consideration, you have been selected for the {role_name} position.

Our team was impressed by your background and we look forward to welcoming you onboard.

Someone from our team will reach out shortly with next steps.

Congratulations once again!

Best regards,
The Hiring Team"""
    return subject, body


def rejection_template(first_name: str, role_name: str) -> tuple[str, str]:
    subject = f"Your application for {role_name}"
    body = f"""Hi {first_name},

Thank you for taking the time to apply for the {role_name} position and for your interest in joining our team.

After careful review of all applications, we have decided to move forward with another candidate whose experience more closely matches our current needs.

We truly appreciate the effort you put into your application and encourage you to apply for future openings that align with your skills.

We wish you all the best in your job search.

Kind regards,
The Hiring Team"""
    return subject, body


def interview_template(first_name: str, role_name: str) -> tuple[str, str]:
    subject = f"Interview Invitation – {role_name}"
    body = f"""Hi {first_name},

We are pleased to invite you for an interview for the {role_name} position.

[Please add interview date, time, format (in-person/video), and any instructions here.]

Please confirm your availability by replying to this email.

Looking forward to speaking with you!

Best regards,
The Hiring Team"""
    return subject, body


# ── Send functions ─────────────────────────────────────────────────────────────

def send_hired_email(to_email: str, first_name: str, role_name: str):
    subject, body = hired_template(first_name, role_name)
    _send(to_email, subject, body)


def send_rejection_email(to_email: str, first_name: str, role_name: str):
    subject, body = rejection_template(first_name, role_name)
    _send(to_email, subject, body)


def send_interview_email(to_email: str, first_name: str, role_name: str, custom_body: str):
    subject = f"Interview Invitation – {role_name}"
    _send(to_email, subject, custom_body)
