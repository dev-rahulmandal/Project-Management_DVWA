# syntax=docker/dockerfile:1
#
# Prolane web (Next.js 14, App Router) - production standalone build.
# Part of a DELIBERATELY-VULNERABLE training target; local use only.
#
# Build context is the repo root (see docker-compose.yml).

# --- deps: install node_modules from the lockfile (cached layer) -------------
FROM node:20-slim AS deps
WORKDIR /app
COPY web/package.json web/package-lock.json ./
RUN npm ci

# --- builder: compile the production bundle ----------------------------------
FROM node:20-slim AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY web ./

# Browser-facing API origin is INLINED into the client bundle at build time,
# so it is fixed in the image. Default targets the host's published api port.
ARG NEXT_PUBLIC_API_ORIGIN=http://localhost:8081
ENV NEXT_PUBLIC_API_ORIGIN=$NEXT_PUBLIC_API_ORIGIN
RUN npm run build

# --- runner: minimal self-contained server -----------------------------------
FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=8082 \
    HOSTNAME=0.0.0.0

# The standalone output bundles only the server + traced node_modules.
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 8082
CMD ["node", "server.js"]
