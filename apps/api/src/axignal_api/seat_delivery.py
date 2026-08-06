from __future__ import annotations

import secrets
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from hashlib import sha256
from urllib.parse import urlencode

from axignal_api.seat_config import SeatSettings


@dataclass(frozen=True)
class InvitationSecret:
    token: str
    digest: str


@dataclass(frozen=True)
class DeliveryReceipt:
    provider: str
    delivered: bool
    test_acceptance_token: str | None = None


def create_invitation_secret() -> InvitationSecret:
    token = secrets.token_urlsafe(32)
    return InvitationSecret(
        token=token,
        digest=sha256(token.encode("utf-8")).hexdigest(),
    )


def digest_invitation_token(token: str) -> str:
    if not token or len(token) > 512:
        raise ValueError("Invitation token is invalid")
    return sha256(token.encode("utf-8")).hexdigest()


class SeatInvitationDelivery:
    def __init__(self, settings: SeatSettings) -> None:
        self.settings = settings

    def deliver(
        self,
        *,
        recipient_email: str,
        token: str,
        inviter_email: str,
        expires_at_iso: str,
    ) -> DeliveryReceipt:
        self.settings.require_invitation_delivery()
        if self.settings.invitation_provider == "test":
            return DeliveryReceipt(
                provider="TEST",
                delivered=True,
                test_acceptance_token=token,
            )

        assert self.settings.public_base_url is not None
        assert self.settings.smtp_host is not None
        assert self.settings.smtp_from is not None
        query = urlencode({"token": token})
        acceptance_url = (
            f"{self.settings.public_base_url.rstrip('/')}/accept-invitation?{query}"
        )

        message = EmailMessage()
        message["Subject"] = "Your AXIGNAL organisation invitation"
        message["From"] = self.settings.smtp_from
        message["To"] = recipient_email
        message.set_content(
            "\n".join(
                (
                    f"{inviter_email} invited you to an AXIGNAL organisation.",
                    "",
                    f"Accept the invitation: {acceptance_url}",
                    f"Invitation expires: {expires_at_iso}",
                    "",
                    "The invitation is single-use. Do not forward this link.",
                )
            )
        )

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

        return DeliveryReceipt(provider="SMTP", delivered=True)
