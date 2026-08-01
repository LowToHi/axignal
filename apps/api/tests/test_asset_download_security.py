from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest

from scripts.asset_download_security import (
    AssetDownloadError,
    AssetDownloadPolicy,
    download_asset,
    validate_remote_url,
)

PUBLIC_IP = "93.184.216.34"
URL = "https://assets.example.com/file.bin"


def policy(content: bytes = b"asset", **overrides: object) -> AssetDownloadPolicy:
    values: dict[str, object] = {
        "allowed_hosts": frozenset({"assets.example.com", "cdn.example.com"}),
        "allowed_content_types": frozenset({"application/octet-stream"}),
        "max_bytes": 64,
        "expected_sha256": hashlib.sha256(content).hexdigest(),
        "max_redirects": 2,
    }
    values.update(overrides)
    return AssetDownloadPolicy(**values)  # type: ignore[arg-type]


def resolver(host: str, port: int) -> list[str]:
    assert host in {"assets.example.com", "cdn.example.com"}
    assert port == 443
    return [PUBLIC_IP]


def peer(_: httpx.Response) -> str:
    return PUBLIC_IP


def test_policy_requires_a_pinned_digest() -> None:
    with pytest.raises(AssetDownloadError, match="pinned lowercase SHA-256"):
        policy(expected_sha256="")


@pytest.mark.parametrize(
    "url",
    [
        "http://assets.example.com/file.bin",
        "https://assets.example.com:444/file.bin",
        "https://assets.example.com/file.bin#fragment",
        "https://untrusted.example.net/file.bin",
    ],
)
def test_url_policy_rejects_unsafe_urls(url: str) -> None:
    with pytest.raises(AssetDownloadError):
        validate_remote_url(url, policy(), resolver=resolver)


def test_url_policy_rejects_user_information() -> None:
    userinfo_url = "https://" + "user" + ":" + "pass" + "@assets.example.com/file.bin"
    with pytest.raises(AssetDownloadError, match="user information"):
        validate_remote_url(userinfo_url, policy(), resolver=resolver)


@pytest.mark.parametrize(
    "answers",
    [
        ["127.0.0.1"],
        [PUBLIC_IP, "10.0.0.8"],
    ],
)
def test_url_policy_rejects_private_or_mixed_dns_answers(answers: list[str]) -> None:
    with pytest.raises(AssetDownloadError, match="non-public"):
        validate_remote_url(URL, policy(), resolver=lambda _host, _port: answers)


def test_download_rejects_symbolic_link_destination(tmp_path: Path) -> None:
    target = tmp_path / "target.bin"
    target.write_bytes(b"existing")
    destination = tmp_path / "asset.bin"
    destination.symlink_to(target)
    with pytest.raises(AssetDownloadError, match="symbolic link"):
        download_asset(
            URL,
            destination,
            policy(),
            resolver=resolver,
            peer_address_provider=peer,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    headers={"content-type": "application/octet-stream"},
                    content=b"asset",
                    request=request,
                )
            ),
        )
    assert target.read_bytes() == b"existing"


def test_download_rejects_dns_rebinding_peer(tmp_path: Path) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "application/octet-stream"},
            content=b"asset",
            request=request,
        )
    )
    with pytest.raises(AssetDownloadError, match="differs from validated DNS"):
        download_asset(
            URL,
            tmp_path / "asset.bin",
            policy(),
            resolver=resolver,
            peer_address_provider=lambda _response: "8.8.8.8",
            transport=transport,
        )


def test_download_revalidates_redirect_target(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"location": "https://127.0.0.1/internal"},
            request=request,
        )

    with pytest.raises(AssetDownloadError):
        download_asset(
            URL,
            tmp_path / "asset.bin",
            policy(),
            resolver=resolver,
            peer_address_provider=peer,
            transport=httpx.MockTransport(handler),
        )


def test_download_rejects_redirect_loop(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": URL}, request=request)

    with pytest.raises(AssetDownloadError, match="redirect limit"):
        download_asset(
            URL,
            tmp_path / "asset.bin",
            policy(max_redirects=1),
            resolver=resolver,
            peer_address_provider=peer,
            transport=httpx.MockTransport(handler),
        )


class StreamingBody(httpx.SyncByteStream):
    def __init__(self, content: bytes) -> None:
        self.content = content

    def __iter__(self) -> Iterator[bytes]:
        yield self.content


@pytest.mark.parametrize(
    ("headers", "content", "message", "streaming"),
    [
        ({"content-type": "text/html"}, b"asset", "content type", False),
        (
            {"content-type": "application/octet-stream", "content-length": "65"},
            b"asset",
            "Content-Length",
            False,
        ),
        (
            {"content-type": "application/octet-stream"},
            b"x" * 65,
            "body exceeds",
            True,
        ),
    ],
)
def test_download_rejects_content_contract_violations(
    tmp_path: Path,
    headers: dict[str, str],
    content: bytes,
    message: str,
    streaming: bool,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if streaming:
            return httpx.Response(
                200, headers=headers, stream=StreamingBody(content), request=request
            )
        return httpx.Response(200, headers=headers, content=content, request=request)

    transport = httpx.MockTransport(handler)
    with pytest.raises(AssetDownloadError, match=message):
        download_asset(
            URL,
            tmp_path / "asset.bin",
            policy(),
            resolver=resolver,
            peer_address_provider=peer,
            transport=transport,
        )
    assert not (tmp_path / "asset.bin").exists()
    assert not list(tmp_path.glob("*.part"))


def test_download_rejects_digest_mismatch_and_removes_partial(tmp_path: Path) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "application/octet-stream"},
            content=b"different",
            request=request,
        )
    )
    with pytest.raises(AssetDownloadError, match="digest does not match"):
        download_asset(
            URL,
            tmp_path / "asset.bin",
            policy(),
            resolver=resolver,
            peer_address_provider=peer,
            transport=transport,
        )
    assert not (tmp_path / "asset.bin").exists()
    assert not list(tmp_path.glob("*.part"))


def test_download_succeeds_atomically_after_redirect(tmp_path: Path) -> None:
    content = b"asset"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "assets.example.com":
            return httpx.Response(
                307,
                headers={"location": "https://cdn.example.com/final.bin"},
                request=request,
            )
        return httpx.Response(
            200,
            headers={
                "content-type": "application/octet-stream; charset=binary",
                "content-length": str(len(content)),
            },
            content=content,
            request=request,
        )

    destination = tmp_path / "asset.bin"
    result = download_asset(
        URL,
        destination,
        policy(content),
        resolver=resolver,
        peer_address_provider=peer,
        transport=httpx.MockTransport(handler),
    )
    assert destination.read_bytes() == content
    assert result.redirects == 1
    assert result.bytes_written == len(content)
    assert result.sha256 == hashlib.sha256(content).hexdigest()
    assert result.final_url == "https://cdn.example.com/final.bin"
