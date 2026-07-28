# AXIGNAL security policy

## Reporting

Do not open public issues for suspected vulnerabilities, exposed credentials, tenant-isolation defects or source-right bypasses.

Until a dedicated security mailbox is published, contact the repository owner privately through the verified GitHub account and include:

- affected component and revision;
- reproduction steps;
- impact and prerequisites;
- whether credentials, personal data or customer data may be exposed;
- suggested containment if known.

## Response boundary

AXIGNAL will prioritise:

1. credential or secret exposure;
2. cross-tenant access;
3. canonical claim or provenance tampering;
4. unauthorised source export;
5. code execution or runner compromise;
6. privacy-control bypass;
7. integrity failures in billing or entitlements.

## Secrets

- Never commit `.env` files, production keys or customer data.
- CI uses minimum token permissions.
- Persistent self-hosted runners must not execute untrusted fork code.
- Suspected runner compromise requires credential revocation and host rebuild.

## Supported versions

The project is pre-release. Only the current `main` branch and active release candidates receive security fixes.
