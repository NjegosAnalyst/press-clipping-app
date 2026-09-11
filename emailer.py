"""Slanje email obavještenja preko Gmail SMTP-a."""
import os
import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def send_email(subject, body, to_address=None):
    """Šalje email preko Gmail SMTP-a koristeći GMAIL_ADDRESS/GMAIL_APP_PASSWORD
    iz .env fajla. Ako to_address nije zadan, šalje na GMAIL_ADDRESS (samom sebi)."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        raise RuntimeError("GMAIL_ADDRESS / GMAIL_APP_PASSWORD nisu postavljeni u .env")

    to_address = to_address or GMAIL_ADDRESS

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to_address

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, [to_address], msg.as_string())
