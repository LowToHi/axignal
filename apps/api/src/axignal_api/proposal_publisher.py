from __future__ import annotations

import argparse
import logging
import time

from axignal_api.proposal_queue import (
    ProposalOutboxPublisher,
    ValkeyDocumentProposalQueue,
)
from axignal_api.proposal_repository import DocumentProposalRepository
from axignal_api.settings import Settings

LOGGER = logging.getLogger("axignal.document-proposal-publisher")


def build_publisher(settings: Settings) -> ProposalOutboxPublisher:
    settings.require_persistent_research()
    assert settings.database_url is not None
    assert settings.valkey_url is not None
    repository = DocumentProposalRepository(app_dsn=settings.database_url)
    queue = ValkeyDocumentProposalQueue(
        settings.valkey_url,
        queue_key=settings.proposal_queue_key,
    )
    return ProposalOutboxPublisher(repository, queue)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AXIGNAL document proposal outbox publisher"
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    publisher = build_publisher(Settings.from_env())
    if args.once:
        published = publisher.publish_pending(limit=20)
        LOGGER.info("Published %s document proposal jobs", published)
        return 0

    while True:
        publisher.publish_pending(limit=20)
        time.sleep(max(0.1, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
