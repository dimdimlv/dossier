"""Tests for the Pushgateway metrics layer (ADR-013).

These never touch the network: ``push_to_gateway`` is monkeypatched to capture
the registry, mirroring the project's fake-client pattern for the LLM engine.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from prometheus_client import CollectorRegistry

from dossier import metrics
from dossier.cli import run


def _sample(registry: CollectorRegistry, name: str) -> float | None:
    return registry.get_sample_value(name)


def test_build_registry_sets_gauges() -> None:
    registry = metrics.build_followups_registry(
        total=3, overdue=2, due_today=1, now=1000.0
    )
    assert _sample(registry, "dossier_followups_due_total") == 3
    assert _sample(registry, "dossier_followups_overdue") == 2
    assert _sample(registry, "dossier_followups_due_today") == 1
    assert _sample(registry, "dossier_followups_last_run_timestamp_seconds") == 1000.0
    assert (
        _sample(registry, "dossier_followups_last_success_timestamp_seconds") == 1000.0
    )


def test_build_registry_omits_success_timestamp_on_failure() -> None:
    registry = metrics.build_followups_registry(
        total=0, overdue=0, due_today=0, success=False, now=5.0
    )
    assert _sample(registry, "dossier_followups_last_run_timestamp_seconds") == 5.0
    assert (
        _sample(registry, "dossier_followups_last_success_timestamp_seconds") is None
    )


def test_push_followups_metrics_calls_gateway(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_push(gateway: str, *, job: str, registry: CollectorRegistry) -> None:
        captured["gateway"] = gateway
        captured["job"] = job
        captured["overdue"] = registry.get_sample_value("dossier_followups_overdue")

    monkeypatch.setattr(metrics, "push_to_gateway", fake_push)
    metrics.push_followups_metrics(
        "http://gw:9091", total=2, overdue=2, due_today=0
    )
    assert captured == {
        "gateway": "http://gw:9091",
        "job": metrics.FOLLOWUPS_JOB,
        "overdue": 2.0,
    }


@pytest.fixture
def data_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv("DOSSIER_DATABASE_URL", raising=False)
    monkeypatch.setenv("DOSSIER_DATA_PATH", str(tmp_path))
    assert run(["db", "upgrade"]) == 0
    return tmp_path


def _add_overdue_app() -> None:
    assert (
        run(["track", "add", "--company", "Acme", "--role", "Engineer",
             "--applied-on", "2026-06-01"])
        == 0
    )
    assert run(["track", "remind", "1", "--on", "2026-06-01"]) == 0


def test_cli_push_metrics_pushes_counts(
    data_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _add_overdue_app()
    monkeypatch.setenv("DOSSIER_PUSHGATEWAY_URL", "http://gw:9091")

    pushed: dict[str, int] = {}

    def fake_push(url: str, *, total: int, overdue: int, due_today: int) -> None:
        pushed.update(total=total, overdue=overdue, due_today=due_today)

    monkeypatch.setattr(
        "dossier.metrics.push_followups_metrics", fake_push
    )
    assert run(["track", "followups", "--as-of", "2026-06-10", "--push-metrics"]) == 0
    assert pushed == {"total": 1, "overdue": 1, "due_today": 0}


def test_cli_push_metrics_requires_gateway_url(
    data_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("DOSSIER_PUSHGATEWAY_URL", raising=False)
    assert run(["track", "followups", "--as-of", "2026-06-10", "--push-metrics"]) == 1
    assert "DOSSIER_PUSHGATEWAY_URL" in capsys.readouterr().err
