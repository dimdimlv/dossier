"""Prometheus metrics for Dossier's batch workloads (ADR-013).

Dossier is a CLI, not a server, so there is no endpoint to scrape. The recurring
follow-up reminder job instead *pushes* its metrics to a Prometheus Pushgateway
at the end of each run (``dossier track followups --push-metrics``). Prometheus
then scrapes the gateway.

Pushing is always explicit and opt-in: nothing here touches the network unless a
caller passes a gateway URL, which keeps the rest of the CLI (and the test suite)
hermetic.
"""

from __future__ import annotations

import time

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

#: Pushgateway grouping job label for the follow-up reminder digest.
FOLLOWUPS_JOB = "dossier_followups"


def build_followups_registry(
    *,
    total: int,
    overdue: int,
    due_today: int,
    success: bool = True,
    now: float | None = None,
) -> CollectorRegistry:
    """Build a registry holding the follow-up digest gauges.

    Separated from the push so tests can assert on the gauges without a gateway.
    """
    timestamp = time.time() if now is None else now
    registry = CollectorRegistry()

    Gauge(
        "dossier_followups_due_total",
        "Applications with a follow-up due as of the run.",
        registry=registry,
    ).set(total)
    Gauge(
        "dossier_followups_overdue",
        "Applications whose follow-up date is in the past.",
        registry=registry,
    ).set(overdue)
    Gauge(
        "dossier_followups_due_today",
        "Applications whose follow-up date is the run date.",
        registry=registry,
    ).set(due_today)
    Gauge(
        "dossier_followups_last_run_timestamp_seconds",
        "Unix time of the last follow-up digest run.",
        registry=registry,
    ).set(timestamp)
    if success:
        Gauge(
            "dossier_followups_last_success_timestamp_seconds",
            "Unix time of the last successful follow-up digest run.",
            registry=registry,
        ).set(timestamp)
    return registry


def push_followups_metrics(
    gateway_url: str,
    *,
    total: int,
    overdue: int,
    due_today: int,
    success: bool = True,
) -> None:
    """Push the follow-up digest gauges to the Pushgateway at ``gateway_url``."""
    registry = build_followups_registry(
        total=total, overdue=overdue, due_today=due_today, success=success
    )
    push_to_gateway(gateway_url, job=FOLLOWUPS_JOB, registry=registry)
