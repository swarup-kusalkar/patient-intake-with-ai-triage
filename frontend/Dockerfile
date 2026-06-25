# syntax=docker/dockerfile:1
# =============================================================
# Frontend Dockerfile — Multi-stage build
# Stage 1: node:20-alpine builds the Vite SPA
# Stage 2: nginx:alpine serves the built assets + proxies /api
# =============================================================

# -----------------------------------------------------------
# Stage 1: Build
# -----------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first for Docker layer caching
# (only reinstalls deps when package.json / package-lock.json changes)
COPY package.json package-lock.json* ./
RUN npm ci --silent

# Copy the rest of the source and build
COPY . .
RUN npm run build

# -----------------------------------------------------------
# Stage 2: Serve with nginx
# -----------------------------------------------------------
FROM nginx:alpine AS runner

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom nginx config
COPY nginx.conf /etc/nginx/conf.d/app.conf

# Copy the built SPA from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80 (docker-compose maps 3000:80)
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
