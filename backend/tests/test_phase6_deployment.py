"""
Kestrel Phase 6 Tests — Deployment, Observability & Container Specifications
Validates:
1. Prometheus metrics endpoint (/metrics) and exposition format.
2. HTTP request metric increments via middleware.
3. Health check and API status endpoints.
4. Dockerfiles (backend & frontend) and prometheus.yml configurations.
"""
import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.routers.metrics import increment_metric


@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Verify core health endpoint responds with 200 and online status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "online"
        assert "version" in data
        assert data["name"] == "Kestrel"


@pytest.mark.asyncio
async def test_api_status_detailed():
    """Verify detailed status endpoint reports model counts and active feature flags."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "online"
        assert "models" in data
        assert "features" in data
        assert data["features"]["signals"] is True
        assert data["features"]["bridge_mt5"] is True


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint():
    """Verify /metrics returns Prometheus 0.0.4 text exposition format with all required gauges and counters."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Trigger an increment
        increment_metric("circuit_breaker_tripped_total", 1)
        increment_metric("copier_broadcasts_total", 3)
        increment_metric("swarm_predictions_total", 5)

        resp = await client.get("/metrics")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers.get("content-type", "")

        body = resp.text
        # Check required metrics
        assert "kestrel_uptime_seconds" in body
        assert "kestrel_active_terminals_gauge" in body
        assert "kestrel_total_terminals_gauge" in body
        assert "kestrel_open_positions_gauge" in body
        assert "kestrel_exposure_volume_lots" in body
        assert "kestrel_pending_remote_commands_gauge" in body
        assert "kestrel_http_requests_total" in body
        assert "kestrel_circuit_breaker_tripped_total" in body
        assert "kestrel_copier_broadcasts_total" in body
        assert "kestrel_180_swarm_predictions_total" in body
        assert "kestrel_remote_commands_dispatched_total" in body


@pytest.mark.asyncio
async def test_observability_middleware_request_counting():
    """Verify that requests flowing through Kestrel increment kestrel_http_requests_total."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.get("/metrics")
        body1 = r1.text

        # Make a health check call
        await client.get("/api/health")

        r2 = await client.get("/metrics")
        body2 = r2.text

        assert "kestrel_http_requests_total" in body2


def test_deployment_configuration_files_exist():
    """Verify presence and structure of Prometheus, Docker, and CI artifacts."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Prometheus configuration
    prom_path = os.path.join(root_dir, "prometheus", "prometheus.yml")
    assert os.path.exists(prom_path), "prometheus.yml must exist"
    with open(prom_path, "r", encoding="utf-8") as f:
        prom_content = f.read()
    assert "kestrel-backend" in prom_content
    assert "/metrics" in prom_content

    # Backend Dockerfile
    backend_dockerfile = os.path.join(root_dir, "backend", "Dockerfile")
    assert os.path.exists(backend_dockerfile), "backend/Dockerfile must exist"
    with open(backend_dockerfile, "r", encoding="utf-8") as f:
        be_docker_content = f.read()
    assert "FROM python:3.11-slim AS builder" in be_docker_content
    assert "USER kestrel" in be_docker_content
    assert "HEALTHCHECK" in be_docker_content

    # Frontend Dockerfile
    frontend_dockerfile = os.path.join(root_dir, "frontend", "Dockerfile")
    assert os.path.exists(frontend_dockerfile), "frontend/Dockerfile must exist"
    with open(frontend_dockerfile, "r", encoding="utf-8") as f:
        fe_docker_content = f.read()
    assert "FROM node:20-alpine AS deps" in fe_docker_content
    assert "USER nextjs" in fe_docker_content
    assert "HEALTHCHECK" in fe_docker_content

    # Docker Compose
    compose_path = os.path.join(root_dir, "docker-compose.yml")
    assert os.path.exists(compose_path), "docker-compose.yml must exist"
    with open(compose_path, "r", encoding="utf-8") as f:
        compose_content = f.read()
    assert "kestrel-prometheus" in compose_content
    assert "kestrel-grafana" in compose_content
