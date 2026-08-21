from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def email_configured() -> bool:
    return bool(settings.SMTP_HOST)


def send_email(*, to: str, subject: str, html: str, text: str | None = None) -> bool:
    if not email_configured():
        logger.info("SMTP not configured; skipped email to %s subject=%s", to, subject)
        return False

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text or subject)
    message.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            if settings.SMTP_TLS:
                smtp.starttls()
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to)
        return False


def send_verification_email(*, to: str, name: str, token: str) -> bool:
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    return send_email(
        to=to,
        subject="Verify your Kanban email",
        text=f"Hi {name}, verify your email: {link}",
        html=f"<p>Hi {name},</p><p><a href='{link}'>Verify your email</a></p>",
    )


def send_invite_email(*, to: str, workspace_name: str, invite_url: str, inviter_name: str) -> bool:
    return send_email(
        to=to,
        subject=f"Join {workspace_name} on Kanban",
        text=f"{inviter_name} invited you to {workspace_name}: {invite_url}",
        html=(
            f"<p>{inviter_name} invited you to <strong>{workspace_name}</strong>.</p>"
            f"<p><a href='{invite_url}'>Accept invite</a></p>"
        ),
    )


def send_notification_email(*, to: str, title: str, body: str, link: str | None = None) -> bool:
    html = f"<p>{body}</p>"
    if link:
        html += f"<p><a href='{link}'>Open in Kanban</a></p>"
    return send_email(to=to, subject=title, text=body, html=html)
