"""
Kestrel Observability — Prometheus Metrics Endpoint
Exposes production Prometheus metrics for system health, MT5 terminal states,
open positions, swarm inference rates, and circuit breaker trip events.
"""
import time
from fastapi import APIRouter, Response
from sqlalchemy import select, func
from app.db.database import async_session
from app.models.models import MT5Terminal, LivePosition, RemoteCommand

router = APIRouter(tags=["Observability"])

# In-memory performance and activity counters
START_TIME = time.time()
_metrics_counters = {
    "http_requests_total": 0,
    "circuit_breaker_tripped_total": 0,
    "copier_broadcasts_total": 0,
    "swarm_predictions_total": 0,
    "remote_commands_dispatched_total": 0,
}


def increment_metric(name: str, count: int = 1):
    """Safely increment an in-memory observability metric."""
    if name in _metrics_counters:
        _metrics_counters[name] += count


@router.get("/metrics")
async def get_prometheus_metrics():
    """
    Exposes metrics in standard Prometheus exposition format (text/plain; version=0.0.4).
    Scraped periodically by Prometheus or Datadog/VictoriaMetrics agents.
    """
    uptime_seconds = time.time() - START_TIME
    active_terminals = 0
    total_terminals = 0
    open_positions = 0
    total_exposure_lots = 0.0
    pending_commands = 0

    try:
        async with async_session() as session:
            # Query terminal metrics
            term_stmt = select(func.count(MT5Terminal.id))
            term_res = await session.execute(term_stmt)
            total_terminals = term_res.scalar() or 0

            active_stmt = select(func.count(MT5Terminal.id)).where(MT5Terminal.is_connected == True)
            active_res = await session.execute(active_stmt)
            active_terminals = active_res.scalar() or 0

            # Query live positions metrics
            pos_stmt = select(func.count(LivePosition.id))
            pos_res = await session.execute(pos_stmt)
            open_positions = pos_res.scalar() or 0

            vol_stmt = select(func.sum(LivePosition.volume))
            vol_res = await session.execute(vol_stmt)
            total_exposure_lots = float(vol_res.scalar() or 0.0)

            # Query pending remote commands
            cmd_stmt = select(func.count(RemoteCommand.id)).where(RemoteCommand.status == "PENDING")
            cmd_res = await session.execute(cmd_stmt)
            pending_commands = cmd_res.scalar() or 0
    except Exception:
        # Graceful fallback if database is momentarily unreachable during scraper probe
        pass

    # Build Prometheus Text Exposition Format (version 0.0.4)
    lines = [
        "# HELP kestrel_uptime_seconds Total runtime of Kestrel Core API in seconds.",
        "# TYPE kestrel_uptime_seconds gauge",
        f"kestrel_uptime_seconds {uptime_seconds:.2f}",
        "",
        "# HELP kestrel_active_terminals_gauge Currently connected and synced MT5 terminal instances.",
        "# TYPE kestrel_active_terminals_gauge gauge",
        f"kestrel_active_terminals_gauge {active_terminals}",
        "",
        "# HELP kestrel_total_terminals_gauge Registered MT5 terminals in Kestrel platform.",
        "# TYPE kestrel_total_terminals_gauge gauge",
        f"kestrel_total_terminals_gauge {total_terminals}",
        "",
        "# HELP kestrel_open_positions_gauge Realtime aggregate count of open market positions across all terminals.",
        "# TYPE kestrel_open_positions_gauge gauge",
        f"kestrel_open_positions_gauge {open_positions}",
        "",
        "# HELP kestrel_exposure_volume_lots Total aggregate open lot volume across all live positions.",
        "# TYPE kestrel_exposure_volume_lots gauge",
        f"kestrel_exposure_volume_lots {total_exposure_lots:.2f}",
        "",
        "# HELP kestrel_pending_remote_commands_gauge Pending remote execution commands queued for MT5 terminals.",
        "# TYPE kestrel_pending_remote_commands_gauge gauge",
        f"kestrel_pending_remote_commands_gauge {pending_commands}",
        "",
        "# HELP kestrel_http_requests_total Total number of HTTP requests processed by Kestrel Core.",
        "# TYPE kestrel_http_requests_total counter",
        f"kestrel_http_requests_total {_metrics_counters['http_requests_total']}",
        "",
        "# HELP kestrel_circuit_breaker_tripped_total Total times the daily emergency drawdown circuit breaker was tripped.",
        "# TYPE kestrel_circuit_breaker_tripped_total counter",
        f"kestrel_circuit_breaker_tripped_total {_metrics_counters['circuit_breaker_tripped_total']}",
        "",
        "# HELP kestrel_copier_broadcasts_total Total copy trade broadcast events dispatched to slave accounts.",
        "# TYPE kestrel_copier_broadcasts_total counter",
        f"kestrel_copier_broadcasts_total {_metrics_counters['copier_broadcasts_total']}",
        "",
        "# HELP kestrel_180_swarm_predictions_total Total AI ensemble 180-agent swarm predictions generated.",
        "# TYPE kestrel_180_swarm_predictions_total counter",
        f"kestrel_180_swarm_predictions_total {_metrics_counters['swarm_predictions_total']}",
        "",
        "# HELP kestrel_remote_commands_dispatched_total Total remote control commands sent to MT5 terminals.",
        "# TYPE kestrel_remote_commands_dispatched_total counter",
        f"kestrel_remote_commands_dispatched_total {_metrics_counters['remote_commands_dispatched_total']}",
        "",
    ]

    content = "\n".join(lines) + "\n"
    return Response(
        content=content,
        media_type="text/plain; version=0.0.4; charset=utf-8",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )
