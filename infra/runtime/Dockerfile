FROM python:3.13-slim@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/apps/api/src

WORKDIR /app
COPY requirements/python-runtime.lock /app/requirements/python-runtime.lock
RUN python -m pip --version | grep -F "pip 26.1.2 " \
    && python -m pip install \
        --no-cache-dir \
        --require-hashes \
        --only-binary=:all: \
        --requirement /app/requirements/python-runtime.lock

COPY apps/api/src /app/apps/api/src

RUN useradd --create-home --uid 10001 axignal \
    && mkdir -p /var/lib/axignal/objects \
    && chown -R axignal:axignal /var/lib/axignal

USER axignal
CMD ["python", "-m", "axignal_api.scheduler_service"]
