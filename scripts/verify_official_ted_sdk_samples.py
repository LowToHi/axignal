from __future__ import annotations

import io
import json
import zipfile
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse

import httpx
from defusedxml import ElementTree as SafeElementTree
from defusedxml.common import DefusedXmlException

SDK_RELEASE = "1.14.2"
ARCHIVE_URL = (
    "https://github.com/OP-TED/eForms-SDK/archive/refs/tags/1.14.2.zip"
)
MAX_ARCHIVE_BYTES = 120 * 1024 * 1024
MAX_EXAMPLE_BYTES = 2_097_152
OUTPUT = Path("ted-official-sdk-sample-evidence.json")


class OfficialSampleError(RuntimeError):
    pass


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def element_text(root: object, name: str) -> str | None:
    for element in root.iter():
        if local_name(element.tag) == name and element.text and element.text.strip():
            return " ".join(element.text.split())
    return None


def has_element(root: object, name: str) -> bool:
    return any(local_name(element.tag) == name for element in root.iter())


def download_archive() -> bytes:
    response = httpx.get(
        ARCHIVE_URL,
        timeout=60,
        follow_redirects=True,
        headers={"user-agent": "AXIGNAL/0.1 TED-SDK-sample-verifier"},
    )
    if response.status_code != 200:
        raise OfficialSampleError(
            f"Official SDK archive returned status {response.status_code}"
        )
    final = urlparse(str(response.url))
    if final.scheme != "https" or final.hostname not in {
        "github.com",
        "codeload.github.com",
    }:
        raise OfficialSampleError("Official SDK archive redirected outside GitHub")
    content = bytes(response.content)
    if not content or len(content) > MAX_ARCHIVE_BYTES:
        raise OfficialSampleError("Official SDK archive size is outside the budget")
    return content


def main() -> int:
    archive = download_archive()
    correction_hashes: list[str] = []
    result_hashes: list[str] = []
    valid_example_count = 0
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        version_entries = [name for name in bundle.namelist() if name.endswith("/VERSION")]
        if len(version_entries) != 1:
            raise OfficialSampleError("Official SDK archive has no unique VERSION file")
        version = bundle.read(version_entries[0]).decode("utf-8").strip()
        if version != SDK_RELEASE:
            raise OfficialSampleError("Official SDK archive version differs")
        for name in sorted(bundle.namelist()):
            if "/examples/notices/" not in name or not name.endswith(".xml"):
                continue
            raw = bundle.read(name)
            if not raw or len(raw) > MAX_EXAMPLE_BYTES:
                continue
            try:
                root = SafeElementTree.fromstring(raw)
            except (DefusedXmlException, SafeElementTree.ParseError):
                continue
            valid_example_count += 1
            document_type = local_name(root.tag)
            customization_id = element_text(root, "CustomizationID")
            ubl_version = element_text(root, "UBLVersionID")
            notice_id = element_text(root, "ID")
            version_id = element_text(root, "VersionID")
            issue_date = element_text(root, "IssueDate")
            procedure_id = element_text(root, "ContractFolderID")
            profile_complete = all(
                (
                    customization_id == "eforms-sdk-1.14",
                    ubl_version == "2.3",
                    bool(notice_id),
                    bool(version_id),
                    bool(issue_date),
                    bool(procedure_id),
                )
            )
            if not profile_complete:
                continue
            digest = f"sha256:{sha256(raw).hexdigest()}"
            if document_type == "ContractNotice" and has_element(root, "Changes"):
                if has_element(root, "ChangedNoticeIdentifier") and has_element(
                    root, "ReasonCode"
                ):
                    correction_hashes.append(digest)
            if document_type == "ContractAwardNotice":
                subtype = element_text(root, "SubTypeCode")
                if (
                    subtype == "29"
                    and has_element(root, "NoticeResult")
                    and has_element(root, "LotResult")
                ):
                    result_hashes.append(digest)
    if not correction_hashes:
        raise OfficialSampleError(
            "SDK 1.14.2 contains no complete Change example for the promotion gate"
        )
    if not result_hashes:
        raise OfficialSampleError(
            "SDK 1.14.2 contains no complete subtype-29 result example"
        )
    evidence = {
        "sdk_release": SDK_RELEASE,
        "archive_url": ARCHIVE_URL,
        "archive_hash": f"sha256:{sha256(archive).hexdigest()}",
        "valid_xml_example_count": valid_example_count,
        "complete_change_example_count": len(correction_hashes),
        "complete_result_29_example_count": len(result_hashes),
        "change_example_hashes": correction_hashes,
        "result_29_example_hashes": result_hashes,
        "raw_xml_persisted": False,
        "notice_values_persisted": False,
        "source_product_profile": "ted-eforms-non-personal@1.0.0",
    }
    OUTPUT.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
