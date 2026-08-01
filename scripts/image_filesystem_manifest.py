from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tarfile
from pathlib import PurePosixPath
from typing import BinaryIO


def normalise_prefix(value: str) -> str:
    path = "/" + value.strip("/")
    return path if path != "" else "/"


def selected(name: str, prefixes: tuple[str, ...]) -> bool:
    canonical = "/" + name.lstrip("./")
    return any(
        canonical == prefix or canonical.startswith(prefix.rstrip("/") + "/")
        for prefix in prefixes
    )


def digest_stream(stream: BinaryIO) -> str:
    digest = hashlib.sha256()
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest()


def build_manifest(archive: BinaryIO, prefixes: tuple[str, ...]) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    with tarfile.open(fileobj=archive, mode="r|*") as tar:
        for member in tar:
            if not selected(member.name, prefixes):
                continue
            canonical = str(PurePosixPath("/" + member.name.lstrip("./")))
            entry: dict[str, object] = {
                "path": canonical,
                "mode": member.mode,
                "uid": member.uid,
                "gid": member.gid,
                "size": member.size,
            }
            if member.isreg():
                extracted = tar.extractfile(member)
                if extracted is None:
                    raise RuntimeError(f"cannot read regular file {canonical}")
                entry["type"] = "file"
                entry["sha256"] = digest_stream(extracted)
            elif member.issym():
                entry["type"] = "symlink"
                entry["target"] = member.linkname
            elif member.islnk():
                entry["type"] = "hardlink"
                entry["target"] = member.linkname
            elif member.isdir():
                entry["type"] = "directory"
            else:
                entry["type"] = "other"
                entry["tar_type"] = (
                    member.type.decode("latin1")
                    if isinstance(member.type, bytes)
                    else str(member.type)
                )
            entries.append(entry)

    entries.sort(key=lambda item: (str(item["path"]), str(item["type"])))
    encoded = json.dumps(entries, separators=(",", ":"), sort_keys=True).encode()
    return {
        "schema": "axignal.image-filesystem-manifest.v1",
        "prefixes": list(prefixes),
        "entry_count": len(entries),
        "manifest_sha256": hashlib.sha256(encoded).hexdigest(),
        "entries": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    prefixes = tuple(sorted({normalise_prefix(value) for value in args.prefix}))
    manifest = build_manifest(sys.stdin.buffer, prefixes)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(
        json.dumps(
            {
                "status": "PASS",
                "output": args.output,
                "entry_count": manifest["entry_count"],
                "manifest_sha256": manifest["manifest_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
