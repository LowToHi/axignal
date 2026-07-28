from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import psycopg
from fastapi import APIRouter, HTTPException
from redis import Redis
from redis.exceptions import RedisError

router = APIRouter(tags=["operations"])


def _database_ready() -> bool:
    database_url = os.environ.get("AXIGNAL_DATABASE_URL")
    if not database_url:
        return False
    with (
        psycopg.connect(database_url, connect_timeout=3) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SELECT 1")
        return cursor.fetchone() == (1,)


def _valkey_ready() -> bool:
    valkey_url = os.environ.get("AXIGNAL_VALKEY_URL")
    if not valkey_url:
        return False
    client = Redis.from_url(
        valkey_url,
        socket_connect_timeout=3,
        socket_timeout=3,
        decode_responses=True,
    )
    try:
        return bool(client.ping())
    finally:
        client.close()


def _object_store_ready() -> bool:
    backend = os.environ.get("AXIGNAL_OBJECT_STORE_BACKEND", "local")
    if backend != "local":
        return True
    root = Path(os.environ.get("AXIGNAL_OBJECT_STORE_ROOT", ".axignal/objects"))
    root.mkdir(parents=True, exist_ok=True)
    probe = root / ".pilot-readiness"
    probe.write_text("ok", encoding="utf-8")
    probe.unlink()
    return True


@router.get("/healthz")
def liveness() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "axignal-api",
        "pilot_mode": os.environ.get("AXIGNAL_PILOT_MODE", "false").lower() == "true",
        "build_sha": os.environ.get("AXIGNAL_BUILD_SHA", "unknown"),
    }


@router.get("/readyz")
def readiness() -> dict[str, Any]:
    checks: dict[str, bool] = {}
    try:
        checks["postgres"] = _database_ready()
        checks["valkey"] = _valkey_ready()
        checks["object_store"] = _object_store_ready()
    except (OSError, psycopg.Error, RedisError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="AXIGNAL_PILOT_NOT_READY") from exc

    if not all(checks.values()):
        raise HTTPException(status_code=503, detail="AXIGNAL_PILOT_NOT_READY")
    return {"status": "ready", "checks": checks}
