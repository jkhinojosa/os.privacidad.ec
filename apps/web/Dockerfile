# ===========================================================
# OS Privacidad — Web Dockerfile (Multi-stage)
# ===========================================================
# Stage 1: Dependencies (pnpm install)
# Stage 2: Development (Next.js dev server con HMR)
# Stage 3: Builder (producción build)
# Stage 4: Production (standalone output)
# ===========================================================

# ── Stage 1: Dependencies ────────────────────────────────────
FROM node:22-alpine AS deps

RUN corepack enable && corepack prepare pnpm@11 --activate

WORKDIR /app

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile


# ── Stage 2: Development ─────────────────────────────────────
FROM node:22-alpine AS development

RUN corepack enable && corepack prepare pnpm@11 --activate

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

EXPOSE 3000

CMD ["pnpm", "dev"]


# ── Stage 3: Builder (producción) ────────────────────────────
FROM node:22-alpine AS builder

RUN corepack enable && corepack prepare pnpm@11 --activate

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

RUN pnpm build


# ── Stage 4: Production ──────────────────────────────────────
FROM node:22-alpine AS production

# Crear usuario no-root
RUN addgroup --system --gid 1001 nextjs && \
    adduser --system --uid 1001 nextjs

WORKDIR /app

# Copiar artefactos de build
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /app/.next/static ./.next/static

USER nextjs

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

EXPOSE 3000

CMD ["node", "server.js"]
