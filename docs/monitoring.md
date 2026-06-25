# Monitoring

What Dossier exposes and how it is visualised. Rationale:
[ADR-013](adr/ADR-013-observability.md).

Dossier is a batch CLI, so it has no scrape endpoint. The scheduled follow-up digest **pushes** its
metrics to a Prometheus **Pushgateway** at the end of each run; Prometheus scrapes the gateway
(`honor_labels: true`, so the `job="dossier_followups"` label is preserved). Host and container
health come from node_exporter and cAdvisor.

## Emitting metrics

```bash
DOSSIER_PUSHGATEWAY_URL=http://pushgateway:9091 dossier track followups --push-metrics
```

Without `--push-metrics` the command behaves exactly as before and makes no network calls. With the
flag set but `DOSSIER_PUSHGATEWAY_URL` unset, it exits with a configuration error. The scheduled
Ofelia job (`deploy/ofelia.ini`) sets both.

## Application metrics

All carry the label `job="dossier_followups"`.

| Metric | Meaning |
|---|---|
| `dossier_followups_due_total` | Applications with a follow-up due as of the run. |
| `dossier_followups_overdue` | Follow-ups whose date is in the past. |
| `dossier_followups_due_today` | Follow-ups due on the run date. |
| `dossier_followups_last_run_timestamp_seconds` | Unix time of the last run. |
| `dossier_followups_last_success_timestamp_seconds` | Unix time of the last **successful** run. |

The most operationally useful signal is **freshness**: `time() -
dossier_followups_last_success_timestamp_seconds`. If it exceeds the schedule interval, the reminder
job has stopped or is failing — even though the CLI never "goes down" in the usual sense.

## Dashboard

`deploy/grafana/dashboards/dossier.json` (provisioned, uid `dossier-overview`) shows:

- Stat panels: overdue, due-today, total due, and time-since-last-success (green/yellow/red).
- Follow-ups over time (overdue vs due-today).
- Monitored targets `up` (Prometheus, Pushgateway, node-exporter, cAdvisor).

The Prometheus datasource is provisioned with the fixed uid `dossier-prometheus`
(`deploy/grafana/provisioning/`).

## Local trial

Bring up the metrics core, push once, and inspect:

```bash
docker compose -f deploy/docker-compose.yml up -d pushgateway prometheus grafana
DOSSIER_PUSHGATEWAY_URL=http://localhost:9091 dossier track followups --push-metrics
# Pushgateway:  http://localhost:9091/metrics   (dossier_followups_* series)
# Prometheus:   http://localhost:9090/targets
# Grafana:      http://localhost:3000           (admin / your password) → "Dossier"
docker compose -f deploy/docker-compose.yml down -v
```
