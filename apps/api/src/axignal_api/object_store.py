from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol


class ObjectStoreError(RuntimeError):
    pass


class ObjectIntegrityError(ObjectStoreError):
    pass


class ObjectAlreadyExistsError(ObjectStoreError):
    pass


class ObjectNotFoundError(ObjectStoreError):
    pass


@dataclass(frozen=True)
class ObjectMetadata:
    key: str
    sha256: str
    size_bytes: int
    content_type: str
    created_at: str


class ObjectStore(Protocol):
    def put(
        self,
        *,
        namespace: str,
        content: bytes,
        content_type: str,
        expected_sha256: str | None = None,
    ) -> ObjectMetadata: ...

    def get(self, key: str) -> bytes: ...

    def head(self, key: str) -> ObjectMetadata: ...

    def verify_hash(self, key: str) -> ObjectMetadata: ...

    def delete_if_unreferenced(self, key: str, *, reference_count: int) -> bool: ...


def sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def content_addressed_key(namespace: str, digest: str) -> str:
    safe_namespace = namespace.strip().replace("\\", "/").strip("/")
    if not safe_namespace or ".." in safe_namespace.split("/"):
        raise ValueError("Object namespace is invalid")
    if not re_fullmatch_hex(digest):
        raise ValueError("Object digest must be a lowercase SHA-256 hex value")
    return f"{safe_namespace}/sha256/{digest}"


def re_fullmatch_hex(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


class InMemoryObjectStore:
    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}
        self._metadata: dict[str, ObjectMetadata] = {}

    def put(
        self,
        *,
        namespace: str,
        content: bytes,
        content_type: str,
        expected_sha256: str | None = None,
    ) -> ObjectMetadata:
        digest = sha256_hex(content)
        if expected_sha256 is not None and digest != expected_sha256:
            raise ObjectIntegrityError("Object content does not match expected SHA-256")
        key = content_addressed_key(namespace, digest)
        existing = self._objects.get(key)
        if existing is not None and existing != content:
            raise ObjectAlreadyExistsError("Content-addressed object cannot be overwritten")
        metadata = self._metadata.get(key)
        if metadata is None:
            metadata = ObjectMetadata(
                key=key,
                sha256=digest,
                size_bytes=len(content),
                content_type=content_type,
                created_at=datetime.now(UTC).isoformat(),
            )
            self._objects[key] = bytes(content)
            self._metadata[key] = metadata
        return metadata

    def get(self, key: str) -> bytes:
        try:
            content = self._objects[key]
        except KeyError as exc:
            raise ObjectNotFoundError(key) from exc
        metadata = self._metadata[key]
        if sha256_hex(content) != metadata.sha256:
            raise ObjectIntegrityError("Stored object hash differs from metadata")
        return bytes(content)

    def head(self, key: str) -> ObjectMetadata:
        try:
            return self._metadata[key]
        except KeyError as exc:
            raise ObjectNotFoundError(key) from exc

    def verify_hash(self, key: str) -> ObjectMetadata:
        metadata = self.head(key)
        self.get(key)
        return metadata

    def delete_if_unreferenced(self, key: str, *, reference_count: int) -> bool:
        if reference_count < 0:
            raise ValueError("reference_count cannot be negative")
        if reference_count:
            return False
        self._objects.pop(key, None)
        return self._metadata.pop(key, None) is not None


class LocalFilesystemObjectStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _data_path(self, key: str) -> Path:
        relative = Path(key)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Object key is invalid")
        return self.root / f"{key}.blob"

    def _metadata_path(self, key: str) -> Path:
        return self.root / f"{key}.json"

    def put(
        self,
        *,
        namespace: str,
        content: bytes,
        content_type: str,
        expected_sha256: str | None = None,
    ) -> ObjectMetadata:
        digest = sha256_hex(content)
        if expected_sha256 is not None and digest != expected_sha256:
            raise ObjectIntegrityError("Object content does not match expected SHA-256")
        key = content_addressed_key(namespace, digest)
        data_path = self._data_path(key)
        metadata_path = self._metadata_path(key)
        data_path.parent.mkdir(parents=True, exist_ok=True)
        if data_path.exists():
            if data_path.read_bytes() != content:
                raise ObjectAlreadyExistsError("Content-addressed object cannot be overwritten")
            return self.verify_hash(key)

        metadata = ObjectMetadata(
            key=key,
            sha256=digest,
            size_bytes=len(content),
            content_type=content_type,
            created_at=datetime.now(UTC).isoformat(),
        )
        with tempfile.NamedTemporaryFile(dir=data_path.parent, delete=False) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        try:
            os.replace(temporary_path, data_path)
            metadata_path.write_text(
                json.dumps(asdict(metadata), sort_keys=True),
                encoding="utf-8",
            )
        finally:
            temporary_path.unlink(missing_ok=True)
        return metadata

    def get(self, key: str) -> bytes:
        data_path = self._data_path(key)
        if not data_path.exists():
            raise ObjectNotFoundError(key)
        content = data_path.read_bytes()
        metadata = self.head(key)
        if sha256_hex(content) != metadata.sha256:
            raise ObjectIntegrityError("Stored object hash differs from metadata")
        return content

    def head(self, key: str) -> ObjectMetadata:
        metadata_path = self._metadata_path(key)
        if not metadata_path.exists():
            raise ObjectNotFoundError(key)
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        return ObjectMetadata(**payload)

    def verify_hash(self, key: str) -> ObjectMetadata:
        metadata = self.head(key)
        content = self.get(key)
        if len(content) != metadata.size_bytes:
            raise ObjectIntegrityError("Stored object size differs from metadata")
        return metadata

    def delete_if_unreferenced(self, key: str, *, reference_count: int) -> bool:
        if reference_count < 0:
            raise ValueError("reference_count cannot be negative")
        if reference_count:
            return False
        data_path = self._data_path(key)
        metadata_path = self._metadata_path(key)
        existed = data_path.exists() or metadata_path.exists()
        data_path.unlink(missing_ok=True)
        metadata_path.unlink(missing_ok=True)
        return existed


class S3Client(Protocol):
    def put_object(self, **kwargs: Any) -> Any: ...
    def get_object(self, **kwargs: Any) -> Any: ...
    def head_object(self, **kwargs: Any) -> Any: ...
    def delete_object(self, **kwargs: Any) -> Any: ...


class S3CompatibleObjectStore:
    """S3-compatible adapter with an injected client.

    The client is intentionally injected so the core package does not own cloud
    credentials or a provider SDK lifecycle. Production wiring remains behind
    explicit deployment configuration.
    """

    def __init__(self, *, client: S3Client, bucket: str, prefix: str = "") -> None:
        self.client = client
        self.bucket = bucket
        self.prefix = prefix.strip("/")

    def _remote_key(self, key: str) -> str:
        return f"{self.prefix}/{key}" if self.prefix else key

    def put(
        self,
        *,
        namespace: str,
        content: bytes,
        content_type: str,
        expected_sha256: str | None = None,
    ) -> ObjectMetadata:
        digest = sha256_hex(content)
        if expected_sha256 is not None and digest != expected_sha256:
            raise ObjectIntegrityError("Object content does not match expected SHA-256")
        key = content_addressed_key(namespace, digest)
        metadata = ObjectMetadata(
            key=key,
            sha256=digest,
            size_bytes=len(content),
            content_type=content_type,
            created_at=datetime.now(UTC).isoformat(),
        )
        remote_key = self._remote_key(key)
        try:
            existing = self.head(key)
        except ObjectNotFoundError:
            self.client.put_object(
                Bucket=self.bucket,
                Key=remote_key,
                Body=content,
                ContentType=content_type,
                Metadata={
                    "sha256": digest,
                    "created-at": metadata.created_at,
                },
                IfNoneMatch="*",
            )
            return metadata
        if existing.sha256 != digest or existing.size_bytes != len(content):
            raise ObjectAlreadyExistsError("Remote content-addressed object differs")
        return existing

    def get(self, key: str) -> bytes:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=self._remote_key(key))
        except Exception as exc:
            raise ObjectNotFoundError(key) from exc
        body = response["Body"]
        content = body.read() if hasattr(body, "read") else bytes(body)
        metadata = self.head(key)
        if sha256_hex(content) != metadata.sha256:
            raise ObjectIntegrityError("Remote object hash differs from metadata")
        return content

    def head(self, key: str) -> ObjectMetadata:
        try:
            response = self.client.head_object(
                Bucket=self.bucket,
                Key=self._remote_key(key),
            )
        except Exception as exc:
            raise ObjectNotFoundError(key) from exc
        metadata = response.get("Metadata", {})
        digest = metadata.get("sha256")
        if not digest or not re_fullmatch_hex(digest):
            raise ObjectIntegrityError("Remote object lacks valid SHA-256 metadata")
        return ObjectMetadata(
            key=key,
            sha256=digest,
            size_bytes=int(response["ContentLength"]),
            content_type=response.get("ContentType", "application/octet-stream"),
            created_at=metadata.get("created-at", ""),
        )

    def verify_hash(self, key: str) -> ObjectMetadata:
        metadata = self.head(key)
        self.get(key)
        return metadata

    def delete_if_unreferenced(self, key: str, *, reference_count: int) -> bool:
        if reference_count < 0:
            raise ValueError("reference_count cannot be negative")
        if reference_count:
            return False
        try:
            self.head(key)
        except ObjectNotFoundError:
            return False
        self.client.delete_object(Bucket=self.bucket, Key=self._remote_key(key))
        return True
