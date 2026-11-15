# syntax=docker/dockerfile:1
FROM node:22.12.0-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/ ./
RUN --mount=type=secret,id=proxy_ca,target=/run/proxy-ca.pem \
    if [ -f /run/proxy-ca.pem ]; then export NODE_EXTRA_CA_CERTS=/run/proxy-ca.pem; fi; \
    npm ci --cache /tmp/flare-npm-cache && mkdir -p dist/assets && \
    npm run build -- --emptyOutDir false && rm -rf node_modules /tmp/flare-npm-cache

FROM python:3.12.8-slim-bookworm
WORKDIR /app/backend
COPY backend/ ./
RUN --mount=type=secret,id=proxy_ca,target=/run/proxy-ca.pem \
    if [ -f /run/proxy-ca.pem ]; then export PIP_CERT=/run/proxy-ca.pem; fi; pip install --no-cache-dir -r requirements.lock.txt .
COPY --from=frontend /build/frontend/dist /app/frontend/dist
ENV FLARE_STATIC_DIR=/app/frontend/dist
EXPOSE 8100
CMD ["sh", "-c", "alembic upgrade head && python -m flare.seed && uvicorn flare.api:app --host 0.0.0.0 --port 8100"]
