from __future__ import annotations

import hmac
import ipaddress
import re
from hashlib import sha256
from urllib.parse import urlsplit

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_DISPOSABLE_DOMAINS = frozenset(
    {
        "10minutemail.com",
        "guerrillamail.com",
        "maildrop.cc",
        "mailinator.com",
        "temp-mail.org",
        "tempmail.com",
        "yopmail.com",
    }
)
_GMAIL_DOMAINS = frozenset({"gmail.com", "googlemail.com"})


def normalize_email(value: str) -> str:
    normalized = value.strip().casefold()
    if len(normalized) > 320 or not _EMAIL_RE.fullmatch(normalized):
        raise ValueError("email_invalid")
    return normalized


def email_identity_key(value: str) -> str:
    email = normalize_email(value)
    local, domain = email.rsplit("@", 1)
    if domain in _GMAIL_DOMAINS:
        local = local.split("+", 1)[0].replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"


def email_domain(value: str) -> str:
    return normalize_email(value).rsplit("@", 1)[1]


def domain_is_disposable(value: str) -> bool:
    return email_domain(value) in _DISPOSABLE_DOMAINS


def keyed_digest(value: str, *, pepper: str, namespace: str) -> str:
    material = f"{namespace}\x00{value}".encode()
    return hmac.new(pepper.encode(), material, sha256).hexdigest()


def digest_random_token(token: str) -> str:
    if len(token) < 20:
        raise ValueError("token_too_short")
    return sha256(token.encode()).hexdigest()


def normalize_installation_id(value: str) -> str:
    normalized = value.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{20,200}", normalized):
        raise ValueError("installation_id_invalid")
    return normalized


def network_prefix(value: str | None) -> str:
    if not value:
        return "unknown"
    raw = value.strip().split(",", 1)[0].strip()
    try:
        address = ipaddress.ip_address(raw)
    except ValueError:
        return "unknown"
    if isinstance(address, ipaddress.IPv4Address):
        return str(ipaddress.ip_network(f"{address}/24", strict=False))
    return str(ipaddress.ip_network(f"{address}/56", strict=False))


def origin_host(origin: str) -> str:
    parsed = urlsplit(origin)
    if not parsed.hostname:
        raise ValueError("origin_invalid")
    return parsed.hostname.casefold()


def risk_subjects(
    *,
    email: str,
    installation_id: str,
    network: str | None,
    pepper: str,
) -> dict[str, str]:
    normalized = normalize_email(email)
    identity_key = email_identity_key(normalized)
    domain = email_domain(normalized)
    installation = normalize_installation_id(installation_id)
    prefix = network_prefix(network)
    return {
        "email_normalized": normalized,
        "email_hmac": keyed_digest(normalized, pepper=pepper, namespace="email"),
        "email_identity_hmac": keyed_digest(
            identity_key, pepper=pepper, namespace="email-identity"
        ),
        "domain_hmac": keyed_digest(domain, pepper=pepper, namespace="domain"),
        "installation_hmac": keyed_digest(
            installation, pepper=pepper, namespace="installation"
        ),
        "network_hmac": keyed_digest(prefix, pepper=pepper, namespace="network"),
        "disposable_domain": "true" if domain_is_disposable(normalized) else "false",
    }
