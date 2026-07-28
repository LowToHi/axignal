from __future__ import annotations

import json
import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from opentelemetry import context, propagate
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind, Tracer

_SENSITIVE_KEY = re.compile(
    r"(authorization|api[_-]?key|password|secret|token|cookie|document|prompt|email)",
    re.IGNORECASE,
)
_SENSITIVE_VALUE = re.compile(
    r"(bearer\s+[a-z0-9._~-]+|sk-[a-z0-9_-]{8,}|password=|api[_-]?key=)",
    re.IGNORECASE,
)


def sanitize_attributes(attributes: Mapping[str, Any] | None) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in (attributes or {}).items():
        if _SENSITIVE_KEY.search(key):
            sanitized[key] = "[REDACTED]"
            continue
        if isinstance(value, str):
            sanitized[key] = "[REDACTED]" if _SENSITIVE_VALUE.search(value) else value[:512]
        elif isinstance(value, (bool, int, float)):
            sanitized[key] = value
        elif value is None:
            continue
        else:
            encoded = json.dumps(value, sort_keys=True, default=str)
            sanitized[key] = "[REDACTED]" if _SENSITIVE_VALUE.search(encoded) else encoded[:512]
    return sanitized


def contains_secret_material(value: str) -> bool:
    return bool(_SENSITIVE_VALUE.search(value))


@dataclass(frozen=True)
class TraceEnvelope:
    traceparent: str | None = None
    tracestate: str | None = None
    baggage: str | None = None

    def as_dict(self) -> dict[str, str]:
        return {
            key: value
            for key, value in {
                "traceparent": self.traceparent,
                "tracestate": self.tracestate,
                "baggage": self.baggage,
            }.items()
            if value
        }


def inject_trace_envelope() -> TraceEnvelope:
    carrier: dict[str, str] = {}
    propagate.inject(carrier)
    return TraceEnvelope(
        traceparent=carrier.get("traceparent"),
        tracestate=carrier.get("tracestate"),
        baggage=carrier.get("baggage"),
    )


@contextmanager
def attach_trace_envelope(envelope: Mapping[str, str] | None) -> Iterator[None]:
    token = context.attach(propagate.extract(dict(envelope or {})))
    try:
        yield
    finally:
        context.detach(token)


class RedactingSpanProcessor(SpanProcessor):
    def __init__(self, delegate: SpanProcessor) -> None:
        self.delegate = delegate

    def on_start(self, span: Any, parent_context: Any = None) -> None:
        self.delegate.on_start(span, parent_context=parent_context)

    def on_end(self, span: ReadableSpan) -> None:
        self.delegate.on_end(span)

    def shutdown(self) -> None:
        self.delegate.shutdown()

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return self.delegate.force_flush(timeout_millis)


def build_tracer_provider(
    *,
    service_name: str,
    exporter: Any | None = None,
) -> TracerProvider:
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": service_name,
                "service.namespace": "axignal",
                "deployment.environment": "development",
            }
        )
    )
    selected_exporter = exporter or ConsoleSpanExporter()
    provider.add_span_processor(
        RedactingSpanProcessor(SimpleSpanProcessor(selected_exporter))
    )
    return provider


def build_in_memory_telemetry(
    service_name: str = "axignal-f2-acceptance",
) -> tuple[TracerProvider, InMemorySpanExporter]:
    exporter = InMemorySpanExporter()
    return build_tracer_provider(service_name=service_name, exporter=exporter), exporter


def tracer_for(provider: TracerProvider, name: str) -> Tracer:
    return provider.get_tracer(name)


@contextmanager
def start_span(
    tracer: Tracer,
    name: str,
    *,
    attributes: Mapping[str, Any] | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
) -> Iterator[Any]:
    with tracer.start_as_current_span(
        name,
        attributes=sanitize_attributes(attributes),
        kind=kind,
    ) as span:
        yield span


def span_export_is_redacted(spans: list[ReadableSpan]) -> bool:
    for span in spans:
        for key, value in (span.attributes or {}).items():
            if _SENSITIVE_KEY.search(key) and value != "[REDACTED]":
                return False
            if contains_secret_material(str(value)):
                return False
    return True
