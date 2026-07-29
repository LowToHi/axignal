FROM node:22.14.0-alpine AS builder
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json tsconfig.base.json ./
COPY apps ./apps
COPY packages ./packages
RUN pnpm install --frozen-lockfile
RUN pnpm --filter @axignal/landing build

FROM node:22.14.0-alpine AS runner
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
WORKDIR /app
COPY --from=builder --chown=node:node /app/apps/landing/.next/standalone ./
COPY --from=builder --chown=node:node /app/apps/landing/.next/static ./apps/landing/.next/static
USER node
EXPOSE 3000
CMD ["node", "apps/landing/server.js"]
