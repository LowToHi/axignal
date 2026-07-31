from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from urllib.parse import quote

from axignal_api.identity_config import IdentityRuntimeSettings


@dataclass(frozen=True)
class TenderAlertDeliveryReceipt:
    provider: str
    test_confirmation_token: str | None = None


class TenderAlertDelivery:
    def __init__(self, settings: IdentityRuntimeSettings) -> None:
        settings.require_email_delivery()
        self.settings = settings

    def deliver_confirmation(
        self,
        *,
        recipient: str,
        token: str,
        country_code: str,
        sector_slug: str,
    ) -> TenderAlertDeliveryReceipt:
        if self.settings.email_provider == "test":
            return TenderAlertDeliveryReceipt(
                provider="TEST",
                test_confirmation_token=token,
            )
        assert self.settings.public_app_url is not None
        url = (
            f"{self.settings.public_app_url.rstrip('/')}/alerts/confirm"
            f"?token={quote(token, safe='')}"
        )
        message = EmailMessage()
        message["Subject"] = "Confirm your AXIGNAL tender alert"
        message["From"] = self.settings.smtp_from
        message["To"] = recipient
        message.set_content(
            "Confirm your AXIGNAL tender alert.\n\n"
            f"Market: {country_code} · {sector_slug}\n"
            f"{url}\n\n"
            "This confirmation does not create an AXIGNAL account, tenant or trial."
        )
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
        return TenderAlertDeliveryReceipt(provider="SMTP")
