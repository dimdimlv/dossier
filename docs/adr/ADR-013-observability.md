# ADR-013: Observability — Prometheus + Grafana with a Pushgateway for the batch CLI

## Status

Accepted — 2026-06-25

## Context

Milestone M8 adds monitoring (README names Prometheus + Grafana). The challenge is structural:
**Dossier is a CLI/batch tool, not a long-running service**, so there is no HTTP endpoint for
Prometheus to scrape. The workload worth observing is the scheduled **follow-up reminder digest**
(ADR-012) — is it running, succeeding, and how many follow-ups are overdue? We also want basic host
and container health on the VPS. The project values transferable practice and cautious dependencies.

## Considered alternatives

### Getting batch-job metrics into Prometheus

**A. Pushgateway (chosen).** The canonical Prometheus pattern for short-lived/batch jobs: the job
pushes its metrics to a Pushgateway at the end of each run, and Prometheus scrapes the gateway. The
job (`dossier track followups --push-metrics`) emits gauges via the `prometheus_client` library.
Fits a run-to-exit CLI exactly. *Chosen.*

**B. Expose a `/metrics` endpoint in a long-running process.** Would require turning Dossier into a
daemon purely to be scraped — contradicts ADR-010 and the tool's nature. *Rejected.*

**C. node_exporter textfile collector.** The job writes a `.prom` file that node_exporter exposes.
Works, but couples the app to the exporter's filesystem layout and host paths; the Pushgateway is
the purpose-built, more portable mechanism. *Rejected* (kept as a possible alternative).

**D. No app metrics, host/container only.** Simplest, but blind to the actual follow-up workload —
the thing most worth monitoring. *Rejected.*

### Host and container metrics

**A. node_exporter + cAdvisor (chosen).** The standard pair for host (CPU/mem/disk) and
per-container metrics, scraped by Prometheus alongside the gateway. *Chosen.*

### Metrics client dependency

**A. `prometheus_client` (chosen).** The official Python client; tiny, no transitive weight,
provides `CollectorRegistry`/`Gauge`/`push_to_gateway`. Consent for the dependency was obtained when
choosing the Pushgateway approach. *Chosen.* **B. Hand-rolled text format + HTTP POST.** Avoids a
dep but re-implements the exposition format and push protocol. *Rejected.*

## Decision

Run **Prometheus + Grafana + Pushgateway + node_exporter + cAdvisor** as a compose stack
(`deploy/docker-compose.yml`, ADR-012). The follow-up digest pushes gauges to the Pushgateway via a
new `src/dossier/metrics.py` using `prometheus_client`; `dossier track followups --push-metrics`
reads the gateway URL from `DOSSIER_PUSHGATEWAY_URL` (`config.get_pushgateway_url`). Default CLI
behaviour is unchanged and never touches the network, keeping the test suite hermetic (tests
monkeypatch `push_to_gateway`).

Metrics (job label `dossier_followups`):

- `dossier_followups_due_total` — applications with a follow-up due.
- `dossier_followups_overdue` — follow-ups past their date.
- `dossier_followups_due_today` — follow-ups due on the run date.
- `dossier_followups_last_run_timestamp_seconds` — unix time of the last run.
- `dossier_followups_last_success_timestamp_seconds` — unix time of the last successful run
  (its absence/staleness signals a stopped or failing job).

Prometheus scrapes the gateway with `honor_labels: true` so the pushed `job` label is preserved.
Grafana is provisioned with the Prometheus datasource (fixed uid `dossier-prometheus`) and a
**Dossier** dashboard (`deploy/grafana/dashboards/dossier.json`): overdue / due-today / total stats,
time-since-last-success freshness, follow-ups over time, and target health.

## Consequences

### Positive

- The actual follow-up workload is observable: overdue counts and, crucially, **job freshness** — a
  stale `last_success` timestamp means the scheduled reminder stopped running.
- Standard, transferable Prometheus/Grafana stack; dashboards and scrape config are version-controlled.
- One small, official Python dependency; no impact on default CLI behaviour or tests.

### Negative / trade-offs

- The Pushgateway is an extra component and a single point for pushed metrics; fine for one batch job.
- Pushed gauges persist in the gateway until overwritten — acceptable since each run overwrites the
  same group; no per-run instance labels are used.
- The exporters (node_exporter, cAdvisor, Pushgateway, Prometheus) must be kept off the public
  internet; this is called out in `docs/deployment.md` (firewall / reverse-proxy + auth for Grafana).

### Neutral / future options

- Alertmanager rules (overdue follow-ups exist; `last_success` too old; a target down) are a natural
  next step, intentionally deferred from this milestone.

## References

- ADR-010 — Containerization. ADR-012 — Deployment (the compose stack and the scheduled job).
- `docs/monitoring.md` — metrics catalogue and dashboard.
- Prometheus Pushgateway — https://github.com/prometheus/pushgateway
- prometheus_client (Python) — https://github.com/prometheus/client_python
