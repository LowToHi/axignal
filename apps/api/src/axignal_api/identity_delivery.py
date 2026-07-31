from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from urllib.parse import quote

import httpx

from axignal_api.identity_config import IdentityRuntimeSettings


@dataclass(frozen=True)
class EmailDeliveryReceipt:
    provider: str
    test_token: str | None = None


class IdentityEmailDelivery:
    def __init__(self, settings: IdentityRuntimeSettings) -> None:
        settings.require_email_delivery()
        self.settings = settings

    def deliver_verification(self, *, recipient: str, token: str) -> EmailDeliveryReceipt:
        if self.settings.email_provider == "test":
            return EmailDeliveryReceipt(provider="TEST", test_token=token)
        assert self.settings.public_app_url is not None
        url = (
            f"{self.settings.public_app_url.rstrip('/')}/verify-email"
            f"?token={quote(token, safe='')}"
        )
        self._smtp(
            recipient=recipient,
            subject="Verify your AXIGNAL account",
            text=(
                "Verify your AXIGNAL email address and create a passkey.\n\n"
                f"{url}\n\n"
                "This link expires shortly and can be used only once."
            ),
        )
        return EmailDeliveryReceipt(provider="SMTP")

    def deliver_security_notice(
        self,
        *,
        recipient: str,
        event: str,
        detail: str,
    ) -> EmailDeliveryReceipt:
        if self.settings.email_provider == "test":
            return EmailDeliveryReceipt(provider="TEST")
        self._smtp(
            recipient=recipient,
            subject=f"AXIGNAL security notice: {event}",
            text=(
                f"Security event: {event}\n\n{detail}\n\n"
                "Review your active sessions and contact support if this was not you."
            ),
        )
        return EmailDeliveryReceipt(provider="SMTP")

    def _smtp(self, *, recipient: str, subject: str, text: str) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.settings.smtp_from
        message["To"] = recipient
        message.set_content(text)
        assert self.settings.smtp_host is not None
        with smtplib.SMTP(
            self.settings.smtp_host,
            self.settings.smtp_port,
            timeout=10,
        ) as client:
            if self.settings.smtp_starttls:
                client.starttls()
            if self.settings.smtp_username:
                assert self.settings.smtp_password is not None
                client.login(
                    self.settings.smtp_username,
                    self.settings.smtp_password,
                )
            client.send_message(message)


def verify_bot_token(
    *,
    settings: IdentityRuntimeSettings,
    token: str,
    remote_ip: str | None,
) -> None:
    settings.require_bot_verification()
    if settings.bot_provider == "test":
        if token != "axignal-test-bot-pass":
            raise RuntimeError("bot_verification_failed")
        return
    assert settings.turnstile_secret is not None
    payload = {
        "secret": settings.turnstile_secret,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip
    try:
        response = httpx.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data=payload,
            timeout=5.0,
        )
        response.raise_for_status()
        body = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise RuntimeError("bot_verification_unavailable") from exc
    if not isinstance(body, dict) or body.get("success") is not True:
        raise RuntimeError("bot_verification_failed")
