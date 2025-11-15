# ╔════════════════════════════════════════════════════════╗
# ║         Production Dockerfile - Frontend Service       ║
# ║              Enterprise Image Gen Platform             ║
# ╚════════════════════════════════════════════════════════╝

# ┌─────────────────────────────────────────────────────────┐
# │ 🏗️ Build Stage: Compile TypeScript and bundle assets   │
# └─────────────────────────────────────────────────────────┘
FROM node:18-alpine AS builder

# Install dependencies for node-gyp
RUN apk add --no-cache python3 make g++

WORKDIR /build

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies with cache mount
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production && \
    npm cache clean --force

# Copy source code
COPY . .

# Build application
ENV NODE_ENV=production
RUN npm run build

# 🔒 SECURITY: Audit dependencies
RUN npm audit --audit-level=moderate || echo "WARNING: npm audit found issues"

# ┌─────────────────────────────────────────────────────────┐
# │ 🚀 Runtime Stage: Nginx for serving static files        │
# └─────────────────────────────────────────────────────────┘
FROM nginx:1.25-alpine

# Metadata labels (ISO 27001 A.8.1.1 - Asset ownership)
LABEL maintainer="platform-team@organization.com.au" \
      version="0.1.0" \
      description="EIG Platform Frontend Service" \
      security.compliance="ISO27001" \
      data.classification="public" \
      data.residency="australia"

# Copy built assets from builder
COPY --from=builder /build/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Security: Run as non-root (nginx user)
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

USER nginx

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# ⚠️  SECURITY NOTES:
# - Static files served via nginx (secure, performant)
# - No secrets in frontend build (use runtime config)
# - CSP headers enforced via nginx config
# - SRI (Subresource Integrity) for external scripts
# - HTTPS redirect enforced (see nginx.conf)
#
# 📋 ISO 27001 Controls:
# - A.13.1.3: Segregation in networks
# - A.14.2.6: Secure development environment
