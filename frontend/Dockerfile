# syntax=docker/dockerfile:1.6
#
# Multi-stage build for the escalabirras Angular 16 frontend.
#   - Builder: install deps and run `ng build --configuration production`.
#   - Runtime: nginx serves the built `dist/` with SPA fallback, gzip,
#     and proxy-friendly headers.

ARG NODE_VERSION=20-alpine
ARG NGINX_VERSION=1.27-alpine

FROM node:${NODE_VERSION} AS builder
WORKDIR /build

COPY package.json package-lock.json ./
RUN npm ci

COPY angular.json tsconfig.json tsconfig.app.json tsconfig.spec.json \
    tailwind.config.js prettier.config.js ./
COPY src ./src

RUN npm run build -- --configuration production

FROM nginx:${NGINX_VERSION} AS runtime
WORKDIR /usr/share/nginx/html

COPY --from=builder /build/dist ./
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1