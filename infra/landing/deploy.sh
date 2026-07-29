#!/usr/bin/env bash
set -Eeuo pipefail

release_sha="${1:?release SHA required}"
image_tag="${2:?image tag required}"
image_archive="${3:?image archive required}"
bundle_dir="${4:-$(cd "$(dirname "$0")" && pwd)}"

[[ "${release_sha}" =~ ^[0-9a-f]{40}$ ]]
[[ -f "${image_archive}" ]]
[[ -f "${bundle_dir}/compose.yaml" ]]
[[ "$(id -u)" -eq 0 ]]

for command_name in docker curl python3 getent ss; do
  command -v "${command_name}" >/dev/null
 done

docker info >/dev/null
docker compose version >/dev/null

mapfile -t traefik_containers < <(
  docker ps --format '{{.Names}} {{.Image}}' | awk 'tolower($0) ~ /traefik/ {print $1}'
)
[[ "${#traefik_containers[@]}" -eq 1 ]]
traefik_name="${traefik_containers[0]}"
[[ "$(docker inspect --format '{{.HostConfig.NetworkMode}}' "${traefik_name}")" == "host" ]]

dynamic_mount="$(
  docker inspect --format '{{range .Mounts}}{{if eq .Destination "/etc/traefik/dynamic"}}{{.Source}}{{end}}{{end}}' "${traefik_name}"
)"
[[ -n "${dynamic_mount}" && -d "${dynamic_mount}" && -w "${dynamic_mount}" ]]
ss -H -ltn 'sport = :80' | grep -q .
ss -H -ltn 'sport = :443' | grep -q .

resolved_ipv4="$(getent ahostsv4 axignal.com | awk '{print $1}' | sort -u)"
grep -Fxq '187.124.220.48' <<<"${resolved_ipv4}"

traefik_args="$(docker inspect --format '{{range .Config.Cmd}}{{println .}}{{end}}' "${traefik_name}")"
static_config="$(
  docker exec "${traefik_name}" sh -c '
    for candidate in /etc/traefik/traefik.yml /etc/traefik/traefik.yaml; do
      if [ -f "$candidate" ]; then cat "$candidate"; exit 0; fi
    done
    exit 0
  ' 2>/dev/null || true
)"
dynamic_resolvers="$(
  grep -RhoE 'certResolver:[[:space:]]*[A-Za-z0-9_.-]+' "${dynamic_mount}" 2>/dev/null \
    | awk -F: '{gsub(/[[:space:]]/, "", $2); print $2}' \
    | sort -u \
    | paste -sd, - || true
)"

TRAEFIK_ARGS="${traefik_args}" STATIC_CONFIG="${static_config}" DYNAMIC_RESOLVERS="${dynamic_resolvers}" \
python3 - <<'PY' > /tmp/axignal-landing-traefik.env
import os
import re

args = os.environ.get("TRAEFIK_ARGS", "")
static = os.environ.get("STATIC_CONFIG", "")
dynamic_resolvers = {
    item for item in os.environ.get("DYNAMIC_RESOLVERS", "").split(",") if item
}

entrypoints: dict[str, set[int]] = {}
resolvers: set[str] = set(dynamic_resolvers)

for name, port in re.findall(r"--entrypoints\.([A-Za-z0-9_.-]+)\.address=[^\n]*?:(\d+)", args, re.I):
    entrypoints.setdefault(name, set()).add(int(port))
for name in re.findall(r"--certificatesresolvers\.([A-Za-z0-9_-]+)\.", args, re.I):
    resolvers.add(name)

lines = static.splitlines()
section = None
section_indent = -1
current = None
current_indent = -1
for raw in lines:
    stripped = raw.strip()
    if not stripped or stripped.startswith("#"):
        continue
    indent = len(raw) - len(raw.lstrip())
    if stripped in {"entryPoints:", "certificatesResolvers:"}:
        section = stripped[:-1]
        section_indent = indent
        current = None
        continue
    if section and indent <= section_indent:
        section = None
        current = None
    if not section:
        continue
    child = re.fullmatch(r"([A-Za-z0-9_.-]+):", stripped)
    if child and indent > section_indent:
        if current is None or indent <= current_indent:
            current = child.group(1)
            current_indent = indent
            if section == "certificatesResolvers":
                resolvers.add(current)
            continue
    if section == "entryPoints" and current:
        address = re.match(r"address:\s*[\"']?[^\"']*:(\d+)[\"']?", stripped)
        if address:
            entrypoints.setdefault(current, set()).add(int(address.group(1)))

http_names = sorted(name for name, ports in entrypoints.items() if 80 in ports)
https_names = sorted(name for name, ports in entrypoints.items() if 443 in ports)
resolver_names = sorted(resolvers)

if len(http_names) != 1:
    raise SystemExit(f"expected one Traefik port-80 entrypoint, found {http_names}")
if len(https_names) != 1:
    raise SystemExit(f"expected one Traefik port-443 entrypoint, found {https_names}")
if len(resolver_names) != 1:
    raise SystemExit(f"expected one Traefik certificate resolver, found {resolver_names}")

safe = re.compile(r"^[A-Za-z0-9_.-]+$")
for value in (http_names[0], https_names[0], resolver_names[0]):
    if not safe.fullmatch(value):
        raise SystemExit("unsafe Traefik identifier")

print(f"HTTP_ENTRYPOINT={http_names[0]}")
print(f"HTTPS_ENTRYPOINT={https_names[0]}")
print(f"CERT_RESOLVER={resolver_names[0]}")
PY
# shellcheck disable=SC1091
source /tmp/axignal-landing-traefik.env
rm -f /tmp/axignal-landing-traefik.env

release_root="/opt/axignal/landing"
release_dir="${release_root}/releases/${release_sha}"
intake_dir="/var/lib/axignal/landing/intake"
route_file="${dynamic_mount}/axignal-landing.yml"
route_backup="${release_dir}/previous-traefik.yml"

install -d -m 0750 "${release_root}/releases" "${release_dir}"
install -d -m 0700 -o 1000 -g 1000 "${intake_dir}"
if [[ -e "${intake_dir}/requests.jsonl" ]]; then
  chown 1000:1000 "${intake_dir}/requests.jsonl"
  chmod 0600 "${intake_dir}/requests.jsonl"
fi
install -m 0644 "${bundle_dir}/compose.yaml" "${release_dir}/compose.yaml"
install -m 0750 "${bundle_dir}/deploy.sh" "${release_dir}/deploy.sh"

previous_image=""
previous_sha=""
previous_current=""
if docker inspect axignal-landing >/dev/null 2>&1; then
  previous_image="$(docker inspect --format '{{.Config.Image}}' axignal-landing)"
  previous_sha="$(
    curl -fsS --max-time 3 http://127.0.0.1:18180/api/health 2>/dev/null \
      | python3 -c 'import json,sys; print(json.load(sys.stdin).get("buildSha", "rollback"))' 2>/dev/null || true
  )"
fi
if [[ -L "${release_root}/current" ]]; then
  previous_current="$(readlink -f "${release_root}/current" || true)"
fi
if [[ -f "${route_file}" ]]; then
  cp -a "${route_file}" "${route_backup}"
fi

rollback_required=true
rollback() {
  local exit_code=$?
  set +e
  if [[ -f "${route_backup}" ]]; then
    cp -a "${route_backup}" "${route_file}"
  else
    rm -f "${route_file}"
  fi
  if [[ -n "${previous_image}" ]]; then
    AXIGNAL_LANDING_IMAGE="${previous_image}" \
    AXIGNAL_BUILD_SHA="${previous_sha:-rollback}" \
    AXIGNAL_LANDING_PORT=18180 \
    AXIGNAL_LANDING_INTAKE_DIR="${intake_dir}" \
      docker compose -p axignal-landing -f "${release_dir}/compose.yaml" up -d --remove-orphans
  else
    AXIGNAL_LANDING_IMAGE="${image_tag}" \
    AXIGNAL_BUILD_SHA="${release_sha}" \
    AXIGNAL_LANDING_PORT=18180 \
    AXIGNAL_LANDING_INTAKE_DIR="${intake_dir}" \
      docker compose -p axignal-landing -f "${release_dir}/compose.yaml" down --remove-orphans
  fi
  if [[ -n "${previous_current}" ]]; then
    ln -sfn "${previous_current}" "${release_root}/current"
  else
    rm -f "${release_root}/current"
  fi
  exit "${exit_code}"
}
trap rollback ERR

gzip -dc "${image_archive}" | docker load >/dev/null
docker image inspect "${image_tag}" >/dev/null

export AXIGNAL_LANDING_IMAGE="${image_tag}"
export AXIGNAL_BUILD_SHA="${release_sha}"
export AXIGNAL_LANDING_PORT=18180
export AXIGNAL_LANDING_INTAKE_DIR="${intake_dir}"
docker compose -p axignal-landing -f "${release_dir}/compose.yaml" config -q
docker compose -p axignal-landing -f "${release_dir}/compose.yaml" up -d --remove-orphans

healthy=false
for _ in $(seq 1 48); do
  status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' axignal-landing 2>/dev/null || true)"
  if [[ "${status}" == "healthy" ]]; then
    healthy=true
    break
  fi
  [[ "${status}" != "unhealthy" ]]
  sleep 5
done
[[ "${healthy}" == true ]]

local_health="$(curl -fsS --max-time 8 http://127.0.0.1:18180/api/health)"
HEALTH_JSON="${local_health}" EXPECTED_SHA="${release_sha}" python3 - <<'PY'
import json
import os

health = json.loads(os.environ["HEALTH_JSON"])
assert health["status"] == "ok"
assert health["service"] == "axignal-landing"
assert health["buildSha"] == os.environ["EXPECTED_SHA"]
assert health["intakeConfigured"] is True
PY

route_tmp="$(mktemp "${dynamic_mount}/.axignal-landing.XXXXXX")"
cat > "${route_tmp}" <<EOF
http:
  routers:
    axignal-landing-http:
      rule: "Host(\`axignal.com\`)"
      entryPoints:
        - "${HTTP_ENTRYPOINT}"
      middlewares:
        - axignal-landing-https-redirect
      service: axignal-landing
    axignal-landing-https:
      rule: "Host(\`axignal.com\`)"
      entryPoints:
        - "${HTTPS_ENTRYPOINT}"
      middlewares:
        - axignal-landing-security
      service: axignal-landing
      tls:
        certResolver: "${CERT_RESOLVER}"
  middlewares:
    axignal-landing-https-redirect:
      redirectScheme:
        scheme: https
        permanent: true
    axignal-landing-security:
      headers:
        contentTypeNosniff: true
        frameDeny: true
        referrerPolicy: strict-origin-when-cross-origin
        stsSeconds: 31536000
        stsIncludeSubdomains: true
  services:
    axignal-landing:
      loadBalancer:
        passHostHeader: true
        servers:
          - url: "http://127.0.0.1:18180"
EOF
chmod 0644 "${route_tmp}"
mv -f "${route_tmp}" "${route_file}"

redirect_ready=false
for _ in $(seq 1 24); do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 -H 'Host: axignal.com' http://127.0.0.1/ || true)"
  if [[ "${code}" == "301" || "${code}" == "302" || "${code}" == "307" || "${code}" == "308" ]]; then
    redirect_ready=true
    break
  fi
  sleep 2
done
[[ "${redirect_ready}" == true ]]

https_health=""
for _ in $(seq 1 60); do
  if https_health="$(
    curl -fsS --max-time 10 --resolve axignal.com:443:127.0.0.1 https://axignal.com/api/health 2>/dev/null
  )"; then
    if HEALTH_JSON="${https_health}" EXPECTED_SHA="${release_sha}" python3 - <<'PY'
import json
import os

health = json.loads(os.environ["HEALTH_JSON"])
raise SystemExit(0 if health.get("status") == "ok" and health.get("buildSha") == os.environ["EXPECTED_SHA"] else 1)
PY
    then
      break
    fi
  fi
  https_health=""
  sleep 3
done
[[ -n "${https_health}" ]]

ln -sfn "${release_dir}" "${release_root}/current"
printf '%s\n' "${image_tag}" > "${release_dir}/image.txt"
printf '%s\n' "${release_sha}" > "${release_dir}/sha.txt"

RELEASE_SHA="${release_sha}" IMAGE_TAG="${image_tag}" TRAEFIK_CONTAINER="${traefik_name}" \
HTTP_ENTRYPOINT="${HTTP_ENTRYPOINT}" HTTPS_ENTRYPOINT="${HTTPS_ENTRYPOINT}" CERT_RESOLVER="${CERT_RESOLVER}" \
python3 - <<'PY' > "${release_dir}/deployment-evidence.json"
import json
import os
from datetime import UTC, datetime

evidence = {
    "schema": "axignal.public-landing-deployment.v1",
    "goal_id": "AXIGNAL-GOAL-001",
    "release_sha": os.environ["RELEASE_SHA"],
    "image": os.environ["IMAGE_TAG"],
    "deployed_at": datetime.now(UTC).isoformat(),
    "container": "axignal-landing",
    "loopback_upstream": "127.0.0.1:18180",
    "intake": {
        "backend": "append-only-jsonl",
        "persistent": True,
        "path_disclosed": False,
    },
    "traefik": {
        "container": os.environ["TRAEFIK_CONTAINER"],
        "http_entrypoint": os.environ["HTTP_ENTRYPOINT"],
        "https_entrypoint": os.environ["HTTPS_ENTRYPOINT"],
        "certificate_resolver": os.environ["CERT_RESOLVER"],
    },
    "checks": {
        "container_healthy": True,
        "local_health": True,
        "http_redirect": True,
        "https_certificate_verified": True,
        "https_health": True,
    },
    "rollback_armed_during_transition": True,
    "status": "DEPLOYED_AWAITING_EXTERNAL_SMOKE",
}
print(json.dumps(evidence, indent=2, sort_keys=True))
PY
cp "${release_dir}/deployment-evidence.json" "${bundle_dir}/deployment-evidence.json"
chmod 0640 "${release_dir}/deployment-evidence.json"

rollback_required=false
trap - ERR
