# Public landing release observability

The `Public Landing Release` workflow deploys the exact merged `main` SHA.

After each completed production run, `Public Landing Release Status` publishes the bounded commit status:

```text
axignal/public-landing-release
```

State meanings:

- `success`: the landing was deployed and externally verified through `https://axignal.com/api/health`;
- `failure`: the release failed and the workflow run is the diagnostic source;
- `error`: the release was cancelled.

A successful deployment remains `DEPLOYED_AWAITING_ACCEPTANCE`; this status does not grant private-pilot acceptance or set `REMOTE_PILOT_ACCEPTED`.
