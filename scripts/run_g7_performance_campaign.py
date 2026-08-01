from __future__ import annotations

import argparse
import base64
import concurrent.futures
import hashlib
import hmac
import json
import math
import os
import platform
import shutil
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

CONTRACT_PATH = Path(
    "data/acceptance/performance/AX-G7-performance-capacity-contract.v0.2.json"
)
ASSERTION_VERSION = "v1"
ASSERTION_AUDIENCE = "axignal-api"
TENANTS = (
    UUID("11111111-1111-4111-8111-111111111111"),
    UUID("22222222-2222-4222-8222-222222222222"),
)


@dataclass(frozen=True)
class HttpResult:
    ok: bool
    latency_ms: float
    status: int | None
    body: dict[str, Any] | None
    error: str | None


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def build_assertion(*, secret: str, tenant_id: UUID, subject: str) -> str:
    now = int(time.time())
    payload = {
        "aud": ASSERTION_AUDIENCE,
        "sub": subject,
        "email": f"{subject}@example.test",
        "tenant_id": str(tenant_id),
        "iat": now,
        "exp": now + 300,
    }
    encoded = _b64url(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    )
    signing_input = f"{ASSERTION_VERSION}.{encoded}".encode("ascii")
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{ASSERTION_VERSION}.{encoded}.{_b64url(signature)}"


def request_json(
    *,
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
    timeout: float = 10.0,
) -> HttpResult:
    data = None
    request_headers = dict(headers or {})
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode()
        request_headers.setdefault("content-type", "application/json")
    request = urllib.request.Request(
        url,
        data=data,
        headers=request_headers,
        method=method,
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            body = json.loads(raw) if raw else None
            return HttpResult(
                ok=200 <= response.status < 300,
                latency_ms=(time.perf_counter() - started) * 1000,
                status=response.status,
                body=body,
                error=None,
            )
    except urllib.error.HTTPError as exc:
        return HttpResult(
            ok=False,
            latency_ms=(time.perf_counter() - started) * 1000,
            status=exc.code,
            body=None,
            error=f"HTTPError:{exc.code}",
        )
    except (OSError, TimeoutError, ValueError) as exc:
        return HttpResult(
            ok=False,
            latency_ms=(time.perf_counter() - started) * 1000,
            status=None,
            body=None,
            error=exc.__class__.__name__,
        )


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(fraction * len(ordered)) - 1)
    return ordered[index]


def metric_summary(values: list[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "max": max(values) if values else None,
    }


def http_summary(results: list[HttpResult]) -> dict[str, Any]:
    latencies = [result.latency_ms for result in results]
    errors = sum(not result.ok for result in results)
    statuses = sorted({result.status for result in results}, key=str)
    return {
        "total": len(results),
        "errors": errors,
        "error_rate": errors / len(results) if results else 1.0,
        "latency_ms": metric_summary(latencies),
        "status_counts": {
            str(status): sum(result.status == status for result in results)
            for status in statuses
        },
        "error_counts": {
            error: sum(result.error == error for result in results)
            for error in sorted({result.error for result in results if result.error})
        },
    }


def parse_byte_value(value: str) -> float:
    units = {
        "B": 1.0,
        "kB": 1000.0,
        "KB": 1000.0,
        "KiB": 1024.0,
        "MB": 1000.0**2,
        "MiB": 1024.0**2,
        "GB": 1000.0**3,
        "GiB": 1024.0**3,
    }
    stripped = value.strip()
    for unit in sorted(units, key=len, reverse=True):
        if stripped.endswith(unit):
            number = float(stripped[: -len(unit)].strip())
            return number * units[unit]
    raise ValueError(f"Unsupported byte value: {value}")


def compose_container_ids(project: str) -> list[str]:
    result = subprocess.run(
        [
            "docker",
            "ps",
            "--quiet",
            "--filter",
            f"label=com.docker.compose.project={project}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return [item for item in result.stdout.splitlines() if item]


def service_container_id(project: str, service: str) -> str | None:
    result = subprocess.run(
        [
            "docker",
            "ps",
            "--quiet",
            "--filter",
            f"label=com.docker.compose.project={project}",
            "--filter",
            f"label=com.docker.compose.service={service}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return next((item for item in result.stdout.splitlines() if item), None)


def queue_depth(project: str, queue_key: str) -> int | None:
    container_id = service_container_id(project, "valkey")
    if container_id is None:
        return None
    result = subprocess.run(
        ["docker", "exec", container_id, "valkey-cli", "LLEN", queue_key],
        check=True,
        capture_output=True,
        text=True,
    )
    return int(result.stdout.strip())


def container_restarts(project: str) -> dict[str, int]:
    values: dict[str, int] = {}
    for container_id in compose_container_ids(project):
        result = subprocess.run(
            [
                "docker",
                "inspect",
                "--format",
                "{{.Name}} {{.RestartCount}}",
                container_id,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        name, restart_count = result.stdout.strip().split()
        values[name.lstrip("/")] = int(restart_count)
    return values


def machine_fingerprint() -> dict[str, Any]:
    docker_version = subprocess.run(
        ["docker", "version", "--format", "{{.Server.Version}}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    memory_bytes = None
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        first = meminfo.read_text(encoding="utf-8").splitlines()[0]
        memory_bytes = int(first.split()[1]) * 1024
    disk = shutil.disk_usage("/")
    details = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "memory_bytes": memory_bytes,
        "root_disk_total_bytes": disk.total,
        "docker_server_version": docker_version,
    }
    canonical = json.dumps(details, sort_keys=True, separators=(",", ":"))
    return {
        "details": details,
        "sha256": hashlib.sha256(canonical.encode()).hexdigest(),
    }


class ResourceSampler:
    def __init__(self, *, project: str, queue_key: str, interval_seconds: float) -> None:
        self.project = project
        self.queue_key = queue_key
        self.interval_seconds = interval_seconds
        self.samples: list[dict[str, Any]] = []
        self.errors: list[str] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=self.interval_seconds + 5)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.samples.append(self._sample())
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                self.errors.append(exc.__class__.__name__)
            self._stop.wait(self.interval_seconds)

    def _sample(self) -> dict[str, Any]:
        containers: list[dict[str, Any]] = []
        for container_id in compose_container_ids(self.project):
            result = subprocess.run(
                [
                    "docker",
                    "stats",
                    "--no-stream",
                    "--format",
                    "{{json .}}",
                    container_id,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            row = json.loads(result.stdout)
            used_text, limit_text = row["MemUsage"].split("/", 1)
            used = parse_byte_value(used_text)
            limit = parse_byte_value(limit_text)
            containers.append(
                {
                    "name": row["Name"],
                    "cpu_percent": float(row["CPUPerc"].rstrip("%")),
                    "memory_used_bytes": used,
                    "memory_limit_bytes": limit,
                    "memory_limit_utilisation": used / limit if limit else None,
                }
            )
        return {
            "monotonic_seconds": time.monotonic(),
            "timestamp": datetime.now(UTC).isoformat(),
            "queue_depth": queue_depth(self.project, self.queue_key),
            "containers": containers,
        }


def memory_summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    points: list[tuple[float, float]] = []
    max_utilisation = 0.0
    for sample in samples:
        total = 0.0
        for container in sample["containers"]:
            total += container["memory_used_bytes"]
            utilisation = container.get("memory_limit_utilisation")
            if utilisation is not None:
                max_utilisation = max(max_utilisation, utilisation)
        points.append((sample["monotonic_seconds"], total / 1024**2))
    growth = None
    if len(points) >= 2:
        x_mean = statistics.fmean(point[0] for point in points)
        y_mean = statistics.fmean(point[1] for point in points)
        denominator = sum((point[0] - x_mean) ** 2 for point in points)
        if denominator > 0:
            slope_per_second = sum(
                (point[0] - x_mean) * (point[1] - y_mean)
                for point in points
            ) / denominator
            growth = slope_per_second * 3600
    return {
        "sample_count": len(samples),
        "maximum_limit_utilisation": max_utilisation,
        "growth_mib_per_hour": growth,
        "first_total_mib": points[0][1] if points else None,
        "last_total_mib": points[-1][1] if points else None,
    }


def execute_concurrent_requests(
    *,
    base_url: str,
    path: str,
    count: int,
    concurrency: int,
) -> list[HttpResult]:
    def execute(_: int) -> HttpResult:
        return request_json(url=f"{base_url}{path}", timeout=5)

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        return list(executor.map(execute, range(count)))


def execute_soak(
    *,
    base_url: str,
    duration_seconds: int,
    liveness_requests_per_second: float,
    readiness_interval_seconds: float = 5.0,
) -> tuple[list[HttpResult], list[HttpResult]]:
    liveness: list[HttpResult] = []
    readiness: list[HttpResult] = []
    liveness_interval = 1.0 / max(liveness_requests_per_second, 0.1)
    deadline = time.monotonic() + duration_seconds
    next_liveness = time.monotonic()
    next_readiness = time.monotonic()
    while time.monotonic() < deadline:
        now = time.monotonic()
        if now >= next_liveness:
            liveness.append(request_json(url=f"{base_url}/healthz", timeout=5))
            next_liveness += liveness_interval
        if now >= next_readiness:
            readiness.append(request_json(url=f"{base_url}/readyz", timeout=5))
            next_readiness += readiness_interval_seconds
        delay = min(next_liveness, next_readiness, deadline) - time.monotonic()
        if delay > 0:
            time.sleep(delay)
    return liveness, readiness


def create_research_run(
    *, base_url: str, secret: str, index: int
) -> tuple[UUID, HttpResult]:
    tenant_id = TENANTS[index % len(TENANTS)]
    subject = f"usr_g7_tenant_{index % len(TENANTS) + 1}"
    assertion = build_assertion(
        secret=secret,
        tenant_id=tenant_id,
        subject=subject,
    )
    result = request_json(
        url=f"{base_url}/v1/research-runs",
        method="POST",
        headers={"X-AXIGNAL-Identity-Assertion": assertion},
        payload={
            "context_id": f"ctx_g7_capacity_{index:06d}",
            "opportunity_id": f"opp_g7_capacity_{index:06d}",
            "question": f"G7 bounded capacity observation {index}",
            "include_private_knowledge": False,
        },
        timeout=10,
    )
    if result.ok and result.body is not None:
        result.body["tenant_id"] = str(tenant_id)
        result.body["subject"] = subject
    return tenant_id, result


def execute_research_batch(
    *,
    base_url: str,
    secret: str,
    count: int,
    concurrency: int,
    poll_timeout_seconds: int,
    compose_project: str,
    queue_key: str,
) -> dict[str, Any]:
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        created = list(
            executor.map(
                lambda index: create_research_run(
                    base_url=base_url,
                    secret=secret,
                    index=index,
                ),
                range(count),
            )
        )

    accepted: list[dict[str, Any]] = []
    enqueue_results: list[HttpResult] = []
    tenant_requested = {str(tenant): 0 for tenant in TENANTS}
    for tenant_id, result in created:
        tenant_requested[str(tenant_id)] += 1
        enqueue_results.append(result)
        if result.ok and result.body is not None:
            accepted.append(
                {
                    "run_id": result.body["research_run_id"],
                    "tenant_id": str(tenant_id),
                    "subject": result.body["subject"],
                    "accepted_at": time.monotonic(),
                }
            )

    pending = {run["run_id"]: run for run in accepted}
    terminal: list[dict[str, Any]] = []
    queue_samples: list[int] = []
    deadline = time.monotonic() + poll_timeout_seconds
    next_queue_probe = 0.0
    while pending and time.monotonic() < deadline:
        now = time.monotonic()
        if now >= next_queue_probe:
            depth = queue_depth(compose_project, queue_key)
            if depth is not None:
                queue_samples.append(depth)
            next_queue_probe = now + 0.5
        for run_id, run in list(pending.items()):
            assertion = build_assertion(
                secret=secret,
                tenant_id=UUID(run["tenant_id"]),
                subject=run["subject"],
            )
            result = request_json(
                url=f"{base_url}/v1/research-runs/{run_id}",
                headers={"X-AXIGNAL-Identity-Assertion": assertion},
                timeout=10,
            )
            if result.ok and result.body is not None:
                state = result.body.get("state")
                if state in {"COMPLETED", "FAILED"}:
                    terminal.append(
                        {
                            **run,
                            "state": state,
                            "completion_seconds": time.monotonic() - run["accepted_at"],
                            "error_code": result.body.get("error_code"),
                        }
                    )
                    pending.pop(run_id)
        if pending:
            time.sleep(0.25)

    final_depth = queue_depth(compose_project, queue_key)
    if final_depth is not None:
        queue_samples.append(final_depth)
    elapsed = time.monotonic() - started
    completed = [run for run in terminal if run["state"] == "COMPLETED"]
    tenant_completion: dict[str, list[float]] = {str(tenant): [] for tenant in TENANTS}
    for run in completed:
        tenant_completion[run["tenant_id"]].append(run["completion_seconds"])
    tenant_p95 = {
        tenant: percentile(values, 0.95)
        for tenant, values in tenant_completion.items()
    }
    positive_p95 = [value for value in tenant_p95.values() if value is not None]
    fairness = 0.0
    if len(positive_p95) == len(TENANTS) and max(positive_p95) > 0:
        fairness = min(positive_p95) / max(positive_p95)

    completion_values = [run["completion_seconds"] for run in terminal]
    enqueue_latencies = [result.latency_ms for result in enqueue_results]
    enqueue_errors = sum(not result.ok for result in enqueue_results)
    return {
        "requested": count,
        "accepted": len(accepted),
        "terminal": len(terminal),
        "completed": len(completed),
        "failed": len([run for run in terminal if run["state"] == "FAILED"]),
        "timed_out": len(pending),
        "enqueue_errors": enqueue_errors,
        "enqueue_error_rate": enqueue_errors / count if count else 0.0,
        "enqueue_latency_ms": metric_summary(enqueue_latencies),
        "completion_seconds": metric_summary(completion_values),
        "success_rate": len(completed) / count if count else 0.0,
        "throughput_per_second": len(completed) / elapsed if elapsed else 0.0,
        "elapsed_seconds": elapsed,
        "tenant_requested": tenant_requested,
        "tenant_completed": {
            tenant: len(values) for tenant, values in tenant_completion.items()
        },
        "tenant_completion_p95_seconds": tenant_p95,
        "tenant_fairness_ratio": fairness,
        "queue_peak_observed": max(queue_samples, default=None),
        "queue_samples": queue_samples,
        "terminal_runs": terminal,
    }


def evaluate(
    *,
    profile: dict[str, Any],
    liveness: dict[str, Any],
    readiness: dict[str, Any],
    research: dict[str, Any],
    resources: dict[str, Any],
    queue_peak: int | None,
    queue_residual: int | None,
    restarts: dict[str, int],
    soak_seconds: int,
) -> list[str]:
    thresholds = profile["thresholds"]
    findings: list[str] = []

    def maximum(name: str, actual: float | int | None, expected: float) -> None:
        if actual is None or actual > expected:
            findings.append(f"{name}:{actual}>{expected}")

    def minimum(name: str, actual: float | int | None, expected: float) -> None:
        if actual is None or actual < expected:
            findings.append(f"{name}:{actual}<{expected}")

    minimum(
        "liveness_request_count",
        liveness["total"],
        profile["minimum_liveness_requests"],
    )
    minimum(
        "readiness_request_count",
        readiness["total"],
        profile["minimum_readiness_requests"],
    )
    minimum("research_run_count", research["requested"], profile["minimum_research_runs"])
    minimum("soak_seconds", soak_seconds, profile["minimum_soak_seconds"])
    maximum(
        "liveness_error_rate",
        liveness["error_rate"],
        thresholds["liveness_error_rate_max"],
    )
    maximum(
        "liveness_p95_ms",
        liveness["latency_ms"]["p95"],
        thresholds["liveness_p95_ms_max"],
    )
    maximum(
        "liveness_p99_ms",
        liveness["latency_ms"]["p99"],
        thresholds["liveness_p99_ms_max"],
    )
    maximum(
        "readiness_error_rate",
        readiness["error_rate"],
        thresholds["readiness_error_rate_max"],
    )
    maximum(
        "readiness_p95_ms",
        readiness["latency_ms"]["p95"],
        thresholds["readiness_p95_ms_max"],
    )
    maximum(
        "enqueue_error_rate",
        research["enqueue_error_rate"],
        thresholds["enqueue_error_rate_max"],
    )
    maximum(
        "enqueue_p95_ms",
        research["enqueue_latency_ms"]["p95"],
        thresholds["enqueue_p95_ms_max"],
    )
    minimum(
        "research_success_rate",
        research["success_rate"],
        thresholds["research_success_rate_min"],
    )
    maximum(
        "completion_p95_seconds",
        research["completion_seconds"]["p95"],
        thresholds["completion_p95_seconds_max"],
    )
    maximum(
        "completion_p99_seconds",
        research["completion_seconds"]["p99"],
        thresholds["completion_p99_seconds_max"],
    )
    minimum(
        "tenant_fairness_ratio",
        research["tenant_fairness_ratio"],
        thresholds["tenant_fairness_ratio_min"],
    )
    maximum("queue_peak", queue_peak, thresholds["queue_max_depth_max"])
    maximum("queue_residual", queue_residual, thresholds["queue_residual_max"])
    maximum(
        "container_restarts",
        sum(restarts.values()),
        thresholds["container_restarts_max"],
    )
    maximum(
        "memory_limit_utilisation",
        resources["maximum_limit_utilisation"],
        thresholds["memory_limit_utilisation_max"],
    )
    if "memory_growth_mib_per_hour_max" in thresholds:
        maximum(
            "memory_growth_mib_per_hour",
            resources["growth_mib_per_hour"],
            thresholds["memory_growth_mib_per_hour_max"],
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AXIGNAL G7 capacity campaign")
    parser.add_argument(
        "--profile",
        choices=("CI_CHARACTERISATION", "PRODUCTION_REPRESENTATIVE"),
        required=True,
    )
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--identity-secret", required=True)
    parser.add_argument("--compose-project", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--health-requests", type=int, required=True)
    parser.add_argument("--health-concurrency", type=int, default=20)
    parser.add_argument("--research-runs", type=int, required=True)
    parser.add_argument("--research-concurrency", type=int, default=6)
    parser.add_argument("--poll-timeout-seconds", type=int, default=180)
    parser.add_argument("--soak-seconds", type=int, required=True)
    parser.add_argument("--soak-rps", type=float, default=2.0)
    parser.add_argument("--sample-interval-seconds", type=float, default=5.0)
    parser.add_argument("--queue-key", default="axignal:research:queue:v1")
    args = parser.parse_args()

    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    profile = contract["profiles"][args.profile]
    sampler = ResourceSampler(
        project=args.compose_project,
        queue_key=args.queue_key,
        interval_seconds=args.sample_interval_seconds,
    )
    campaign_started = datetime.now(UTC)
    sampler.start()
    try:
        liveness_burst = execute_concurrent_requests(
            base_url=args.base_url,
            path="/healthz",
            count=args.health_requests,
            concurrency=args.health_concurrency,
        )
        research = execute_research_batch(
            base_url=args.base_url,
            secret=args.identity_secret,
            count=args.research_runs,
            concurrency=args.research_concurrency,
            poll_timeout_seconds=args.poll_timeout_seconds,
            compose_project=args.compose_project,
            queue_key=args.queue_key,
        )
        liveness_soak, readiness = execute_soak(
            base_url=args.base_url,
            duration_seconds=args.soak_seconds,
            liveness_requests_per_second=args.soak_rps,
        )
    finally:
        sampler.stop()

    liveness = http_summary(liveness_burst + liveness_soak)
    readiness_summary = http_summary(readiness)
    residual = queue_depth(args.compose_project, args.queue_key)
    restarts = container_restarts(args.compose_project)
    resources = memory_summary(sampler.samples)
    sampled_queue_peak = max(
        (
            sample["queue_depth"]
            for sample in sampler.samples
            if sample["queue_depth"] is not None
        ),
        default=None,
    )
    queue_candidates = [
        value
        for value in (sampled_queue_peak, research["queue_peak_observed"])
        if value is not None
    ]
    queue_peak = max(queue_candidates, default=None)
    findings = evaluate(
        profile=profile,
        liveness=liveness,
        readiness=readiness_summary,
        research=research,
        resources=resources,
        queue_peak=queue_peak,
        queue_residual=residual,
        restarts=restarts,
        soak_seconds=args.soak_seconds,
    )
    result = {
        "status": "PASS" if not findings else "FAIL",
        "output": "AX_G7_PERFORMANCE_CHARACTERISATION_READY",
        "contract_id": contract["contract_id"],
        "gate": "G7",
        "gate_decision": "IN_PROGRESS",
        "profile": args.profile,
        "closure_authorised": False,
        "human_capacity_acceptance_required": True,
        "public_launch_authorised": False,
        "baseline_sha": contract["baseline"]["authority_sha"],
        "exact_head_sha": args.expected_sha,
        "campaign_started_at": campaign_started.isoformat(),
        "campaign_finished_at": datetime.now(UTC).isoformat(),
        "machine_fingerprint": machine_fingerprint(),
        "liveness": liveness,
        "readiness": readiness_summary,
        "research": research,
        "resources": resources,
        "resource_sample_errors": sampler.errors,
        "queue": {
            "maximum_observed_depth": queue_peak,
            "resource_sampler_peak": sampled_queue_peak,
            "research_polling_peak": research["queue_peak_observed"],
            "residual_depth": residual,
        },
        "container_restarts": restarts,
        "findings": findings,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
