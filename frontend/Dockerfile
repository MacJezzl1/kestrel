# =================================================================
# Kestrel Unified Cockpit — Multi-Stage Production Dockerfile
# Next.js 16 / React 19 Frontend Container
# =================================================================

# ----------------- Stage 1: Install Dependencies ----------------
FROM node:20-alpine AS deps
WORKDIR /app

# Install libc6-compat for alpine compatibility if needed
RUN apk add --no-cache libc6-compat

COPY package.json package-lock.json ./
RUN npm ci

# ----------------- Stage 2: Build Application -------------------
FROM node:20-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set production environment for build optimization
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

RUN npm run build

# ----------------- Stage 3: Production Runner --------------------
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root system user and group
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy static assets and built distribution
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

USER nextjs

EXPOSE 3000

# Alpine native healthcheck probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["npm", "start"]
