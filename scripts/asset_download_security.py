from __future__ import annotations

import hashlib
import ipaddress
import os
import socket
import tempfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx


class AssetDownloadError(RuntimeError):
    """A remote asset violated the fail-closed acquisition policy."""


IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address
Resolver = Callable[[str, int], Iterable[str]]
PeerAddressProvider = Callable[[httpx.Response], str | None]


@dataclass(frozen=True)
class AssetDownloadPolicy:
    allowed_hosts: frozenset[str]
    allowed_content_types: frozenset[str]
    max_bytes: int
    expected_sha256: str
    max_redirects: int = 3
    connect_timeout_seconds: float = 5.0
    read_timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        normalized_hosts = frozenset(_normalize_host(host) for host in self.allowed_hosts)
        normalized_types = frozenset(
            content_type.strip().casefold() for content_type in self.allowed_content_types
        )
        digest = self.expected_sha256.strip().casefold()
        if not normalized_hosts:
            raise AssetDownloadError("At least one exact asset host is required")
        if not normalized_types:
            raise AssetDownloadError("At least one content type is required")
        if self.max_bytes <= 0:
            raise AssetDownloadError("Asset byte limit must be positive")
        if self.max_redirects < 0 or self.max_redirects > 5:
            raise AssetDownloadError("Asset redirect limit must be between zero and five")
        if len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise AssetDownloadError("A pinned lowercase SHA-256 digest is required")
        object.__setattr__(self, "allowed_hosts", normalized_hosts)
        object.__setattr__(self, "allowed_content_types", normalized_types)
        object.__setattr__(self, "expected_sha256", digest)


@dataclass(frozen=True)
class DownloadedAsset:
    final_url: str
    content_type: str
    bytes_written: int
    sha256: str
    redirects: int


def _normalize_host(host: str) -> str:
    value = host.strip().rstrip(".")
    if not value:
        raise AssetDownloadError("Asset host is empty")
    try:
        return value.encode("idna").decode("ascii").casefold()
    except UnicodeError as exc:
        raise AssetDownloadError("Asset host is not valid IDNA") from exc


def default_resolver(host: str, port: int) -> Iterable[str]:
    try:
        records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise AssetDownloadError("Asset host DNS resolution failed") from exc
    return {record[4][0] for record in records}


def default_peer_address(response: httpx.Response) -> str | None:
    stream = response.extensions.get("network_stream")
    if stream is None or not hasattr(stream, "get_extra_info"):
        return None
    server_addr = stream.get_extra_info("server_addr")
    if isinstance(server_addr, tuple) and server_addr:
        return str(server_addr[0])
    if isinstance(server_addr, str):
        return server_addr
    return None


def _parse_global_ip(raw: str) -> IPAddress:
    value = raw.split("%", 1)[0]
    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise AssetDownloadError("Asset host resolved to an invalid IP address") from exc
    if not address.is_global:
        raise AssetDownloadError("Asset host resolved to a non-public IP address")
    return address


def validate_remote_url(
    url: str,
    policy: AssetDownloadPolicy,
    *,
    resolver: Resolver = default_resolver,
) -> tuple[str, frozenset[IPAddress]]:
    if any(ord(character) < 32 for character in url):
        raise AssetDownloadError("Asset URL contains a control character")
    try:
        parsed = urlsplit(url)
    except ValueError as exc:
        raise AssetDownloadError("Asset URL is malformed") from exc
    if parsed.scheme.casefold() != "https":
        raise AssetDownloadError("Asset URL must use HTTPS")
    if not parsed.hostname:
        raise AssetDownloadError("Asset URL host is required")
    if parsed.username is not None or parsed.password is not None:
        raise AssetDownloadError("Asset URL user information is forbidden")
    if parsed.fragment:
        raise AssetDownloadError("Asset URL fragments are forbidden")
    if parsed.port not in {None, 443}:
        raise AssetDownloadError("Asset URL must use the default HTTPS port")
    host = _normalize_host(parsed.hostname)
    if host not in policy.allowed_hosts:
        raise AssetDownloadError("Asset URL host is not allowlisted")
    addresses = frozenset(_parse_global_ip(raw) for raw in resolver(host, 443))
    if not addresses:
        raise AssetDownloadError("Asset host DNS resolution returned no addresses")
    return host, addresses


def _validate_peer(
    response: httpx.Response,
    expected_addresses: frozenset[IPAddress],
    peer_address_provider: PeerAddressProvider,
) -> None:
    raw_peer = peer_address_provider(response)
    if not raw_peer:
        raise AssetDownloadError("Asset transport did not expose its peer address")
    peer = _parse_global_ip(raw_peer)
    if peer not in expected_addresses:
        raise AssetDownloadError("Asset peer address differs from validated DNS results")


def _content_type(response: httpx.Response, policy: AssetDownloadPolicy) -> str:
    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().casefold()
    if content_type not in policy.allowed_content_types:
        raise AssetDownloadError("Asset response content type is not allowlisted")
    return content_type


def _content_length(response: httpx.Response, policy: AssetDownloadPolicy) -> None:
    raw = response.headers.get("content-length")
    if raw is None:
        return
    try:
        length = int(raw)
    except ValueError as exc:
        raise AssetDownloadError("Asset Content-Length is invalid") from exc
    if length < 0 or length > policy.max_bytes:
        raise AssetDownloadError("Asset Content-Length exceeds the byte limit")


def download_asset(
    url: str,
    destination: Path,
    policy: AssetDownloadPolicy,
    *,
    resolver: Resolver = default_resolver,
    peer_address_provider: PeerAddressProvider = default_peer_address,
    transport: httpx.BaseTransport | None = None,
) -> DownloadedAsset:
    if destination.is_symlink():
        raise AssetDownloadError("Asset destination must not be a symbolic link")
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    timeout = httpx.Timeout(
        connect=policy.connect_timeout_seconds,
        read=policy.read_timeout_seconds,
        write=10.0,
        pool=5.0,
    )
    current_url = url
    redirects = 0
    temporary_path: Path | None = None
    headers = {
        "Accept": ", ".join(sorted(policy.allowed_content_types)),
        "Accept-Encoding": "identity",
        "User-Agent": "AXIGNAL-Asset-Acquisition/2.0",
    }

    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            transport=transport,
            trust_env=False,
        ) as client:
            while True:
                _, addresses = validate_remote_url(current_url, policy, resolver=resolver)
                with client.stream("GET", current_url, headers=headers) as response:
                    _validate_peer(response, addresses, peer_address_provider)
                    if response.status_code in {301, 302, 303, 307, 308}:
                        if redirects >= policy.max_redirects:
                            raise AssetDownloadError("Asset redirect limit exceeded")
                        location = response.headers.get("location")
                        if not location:
                            raise AssetDownloadError("Asset redirect is missing Location")
                        current_url = urljoin(current_url, location)
                        validate_remote_url(current_url, policy, resolver=resolver)
                        redirects += 1
                        continue
                    if response.status_code < 200 or response.status_code >= 300:
                        raise AssetDownloadError(
                            f"Asset server returned HTTP {response.status_code}"
                        )
                    content_type = _content_type(response, policy)
                    _content_length(response, policy)
                    digest = hashlib.sha256()
                    total = 0
                    with tempfile.NamedTemporaryFile(
                        mode="wb",
                        dir=destination.parent,
                        prefix=f".{destination.name}.",
                        suffix=".part",
                        delete=False,
                    ) as output:
                        temporary_path = Path(output.name)
                        for chunk in response.iter_bytes(chunk_size=64 * 1024):
                            if not chunk:
                                continue
                            total += len(chunk)
                            if total > policy.max_bytes:
                                raise AssetDownloadError("Asset body exceeds the byte limit")
                            output.write(chunk)
                            digest.update(chunk)
                        output.flush()
                        os.fsync(output.fileno())
                    observed_digest = digest.hexdigest()
                    if observed_digest != policy.expected_sha256:
                        raise AssetDownloadError(
                            "Asset SHA-256 digest does not match the manifest"
                        )
                    os.replace(temporary_path, destination)
                    temporary_path = None
                    return DownloadedAsset(
                        final_url=current_url,
                        content_type=content_type,
                        bytes_written=total,
                        sha256=observed_digest,
                        redirects=redirects,
                    )
    except httpx.HTTPError as exc:
        raise AssetDownloadError("Asset HTTP transport failed") from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
