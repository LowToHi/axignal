FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY apps/api /app/apps/api
RUN python -m pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 axignal \
    && mkdir -p /var/lib/axignal/objects \
    && chown -R axignal:axignal /var/lib/axignal

USER axignal
CMD ["python", "-m", "axignal_api.scheduler_service"]
