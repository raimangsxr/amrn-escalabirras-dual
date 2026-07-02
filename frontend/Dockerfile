# syntax=docker/dockerfile:1.6

FROM node:24-alpine AS build
WORKDIR /app

ARG API_BASE_URL
ENV API_BASE_URL=${API_BASE_URL}

COPY package.json package-lock.json* ./
RUN npm ci

COPY angular.json tsconfig*.json ./
COPY src ./src

RUN sed -i "s|REPLACE_AT_BUILD_TIME|${API_BASE_URL}|g" \
        src/environments/environment.prod.ts

RUN npm run build -- --configuration production

FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY --from=build /app/dist/amrn-escalabirras-team/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --spider http://127.0.0.1:8080/health || exit 1