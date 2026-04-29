from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from flask import current_app


def send_email(*, to: str, subject: str, body_text: str | None = None, body_html: str | None = None):
    if not body_text and not body_html:
        raise ValueError("Email must include body_text or body_html")

    msg = EmailMessage()
    msg["From"] = current_app.config["SMTP_FROM"]
    msg["To"] = to
    msg["Subject"] = subject

    if body_text:
        msg.set_content(body_text)
    else:
        msg.set_content("This email requires an HTML-capable client.")

    if body_html:
        msg.add_alternative(body_html, subtype="html")

    email_mode = (current_app.config.get("EMAIL_MODE") or "smtp").lower()
    if email_mode == "log":
        logger = logging.getLogger(__name__)
        logger.info(
            "EMAIL_MODE=log: to=%s subject=%s from=%s body_text_len=%s body_html_len=%s",
            to,
            subject,
            msg.get("From"),
            len(body_text or ""),
            len(body_html or ""),
        )
        return

    host = current_app.config["SMTP_HOST"]
    port = int(current_app.config["SMTP_PORT"])
    user = current_app.config.get("SMTP_USER") or None
    password = current_app.config.get("SMTP_PASSWORD") or None
    use_tls = bool(current_app.config.get("SMTP_USE_TLS", True))

    with smtplib.SMTP(host, port) as smtp:
        smtp.ehlo()
        if use_tls:
            smtp.starttls()
            smtp.ehlo()
        if user and password:
            smtp.login(user, password)
        smtp.send_message(msg)
