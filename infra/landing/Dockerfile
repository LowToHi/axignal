FROM node:22.14.0-alpine@sha256:9bef0ef1e268f60627da9ba7d7605e8831d5b56ad07487d24d1aa386336d1944 AS builder
ARG AXIGNAL_BUILD_SHA=axignal-local-build
ARG NEXT_SERVER_ACTIONS_ENCRYPTION_KEY
ENV NEXT_TELEMETRY_DISABLED=1
ENV AXIGNAL_BUILD_SHA=${AXIGNAL_BUILD_SHA}
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json tsconfig.base.json ./
COPY apps ./apps
COPY packages ./packages
COPY data/commercial/commercial-runtime-pricing-stripe-runtime.v0.1.json ./data/commercial/commercial-runtime-pricing-stripe-runtime.v0.1.json
RUN pnpm install --frozen-lockfile
RUN mkdir -p apps/landing/.next/cache \
    && node - <<'NODE'
const crypto = require("node:crypto");
const fs = require("node:fs");
const buildSha = process.env.AXIGNAL_BUILD_SHA;
const derive = (purpose, bytes) => crypto
  .createHash("sha256")
  .update(`axignal:${purpose}:${buildSha}`)
  .digest("hex")
  .slice(0, bytes * 2);
fs.writeFileSync(
  "apps/landing/.next/cache/.previewinfo",
  JSON.stringify({
    previewModeId: derive("inactive-preview-id", 16),
    previewModeSigningKey: derive("inactive-preview-signing", 32),
    previewModeEncryptionKey: derive("inactive-preview-encryption", 32),
    expireAt: 4102444800000,
  }),
);
NODE
RUN pnpm --filter @axignal/landing build

FROM node:22.14.0-alpine@sha256:9bef0ef1e268f60627da9ba7d7605e8831d5b56ad07487d24d1aa386336d1944 AS runner
ARG AXIGNAL_BUILD_SHA=axignal-local-build
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV AXIGNAL_BUILD_SHA=${AXIGNAL_BUILD_SHA}
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
WORKDIR /app
COPY --from=builder --chown=node:node /app/apps/landing/.next/standalone ./
COPY --from=builder --chown=node:node /app/apps/landing/.next/static ./apps/landing/.next/static
COPY --from=builder --chown=node:node /app/apps/landing/public ./apps/landing/public
COPY --from=builder --chown=node:node /app/data/commercial/commercial-runtime-pricing-stripe-runtime.v0.1.json ./data/commercial/commercial-runtime-pricing-stripe-runtime.v0.1.json
WORKDIR /app/apps/landing
USER node
EXPOSE 3000
CMD ["node", "server.js"]
