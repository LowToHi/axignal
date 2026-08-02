#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 5 ]; then
  echo "usage: $0 <raw-responses.cms> <recipient-cert.pem> <private-key.pem> <raw-retention.json> <output-dir>" >&2
  exit 64
fi

ciphertext="$1"
certificate="$2"
private_key="$3"
retention_manifest="$4"
output_dir="$5"

for path in "$ciphertext" "$certificate" "$private_key" "$retention_manifest"; do
  test -f "$path" || { echo "missing file: $path" >&2; exit 66; }
done

test ! -e "$output_dir" || { echo "output directory already exists" >&2; exit 73; }
mkdir -m 700 "$output_dir"
tmp_archive="$(mktemp)"
trap 'rm -f "$tmp_archive"' EXIT

expected_ciphertext="$(python - "$retention_manifest" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["ciphertext_sha256"].removeprefix("sha256:"))
PY
)"
actual_ciphertext="$(sha256sum "$ciphertext" | awk '{print $1}')"
test "$actual_ciphertext" = "$expected_ciphertext" || {
  echo "ciphertext digest mismatch" >&2
  exit 65
}

openssl cms -decrypt \
  -binary \
  -inform DER \
  -in "$ciphertext" \
  -recip "$certificate" \
  -inkey "$private_key" \
  -out "$tmp_archive"

expected_plaintext="$(python - "$retention_manifest" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["plaintext_archive_sha256"].removeprefix("sha256:"))
PY
)"
actual_plaintext="$(sha256sum "$tmp_archive" | awk '{print $1}')"
test "$actual_plaintext" = "$expected_plaintext" || {
  echo "plaintext archive digest mismatch" >&2
  exit 65
}

tar -xzf "$tmp_archive" -C "$output_dir"
chmod -R go-rwx "$output_dir"
printf 'decrypted_to=%s\n' "$output_dir"
