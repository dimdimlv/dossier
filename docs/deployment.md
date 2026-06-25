# Deployment runbook

How to run Dossier's scheduled follow-up reminder and its monitoring stack on a VPS.
Design rationale: [ADR-012](adr/ADR-012-deployment.md) (deployment) and
[ADR-013](adr/ADR-013-observability.md) (monitoring).

Dossier is a CLI, so "deployment" means: the published image runs the **follow-up digest** on a
schedule (Ofelia), pushing metrics to a Prometheus + Grafana stack. Generating CVs/letters remains
an on-demand `docker compose run` (see [the README](../README.md#run-in-docker)).

## Prerequisites

- A VPS with Docker Engine + the Compose plugin.
- Your private `dossier-data` checkout on the host (the tracker DB lives under it).
- The image published to GHCR by `.github/workflows/publish.yml` (runs on push to `main`).

## 1. Get the deploy files onto the host

Clone this repo (only `deploy/` is needed) to e.g. `/srv/dossier`:

```bash
git clone https://github.com/dimdimlv/dossier.git /srv/dossier
cd /srv/dossier
```

## 2. Configure

```bash
cp deploy/.env.example deploy/.env
# Edit deploy/.env: set GF_SECURITY_ADMIN_PASSWORD.
```

Edit `deploy/ofelia.ini`:

- `image`  → `ghcr.io/<owner>/dossier:latest`
- `volume` → `<host path to dossier-data>:/data` (e.g. `/srv/dossier-data:/data`)
- `schedule` → `@daily`, `@every 6h`, or a cron expression.

The digest job needs **no LLM API key** — `dossier track followups` only reads the tracker DB and
pushes counts.

## 3. Bring up the stack

```bash
docker compose -f deploy/docker-compose.yml pull
docker compose -f deploy/docker-compose.yml up -d
```

This starts: `scheduler` (Ofelia), `pushgateway`, `prometheus`, `grafana`, `node-exporter`,
`cadvisor`. Verify the scheduled job runs at least once (or trigger it manually):

```bash
docker run --rm --network dossier \
  -e DOSSIER_DATA_PATH=/data -e DOSSIER_PUSHGATEWAY_URL=http://pushgateway:9091 \
  -v /srv/dossier-data:/data ghcr.io/<owner>/dossier:latest \
  track followups --push-metrics
```

Then check Prometheus → Status → Targets are `up`, and open Grafana → the **Dossier** dashboard.

## 4. Security (important)

The exporters and Prometheus/Pushgateway have **no authentication**. Do not expose them publicly:

- Bind the stack to `127.0.0.1` and/or firewall ports `9090/9091/9100/8080` off the public internet.
- Put **Grafana** (3000) behind a reverse proxy with TLS and change the admin password.
- The Docker socket is mounted **read-only** into Ofelia; keep the host single-tenant.

## 5. Updating

`publish.yml` pushes a fresh `:latest` (and `:sha-…`) on every push to `main`. To update:

```bash
docker compose -f deploy/docker-compose.yml pull
docker compose -f deploy/docker-compose.yml up -d
```

Ofelia pulls the job image on each run (`pull = true`), so the scheduled digest tracks `:latest`
automatically. Pin `deploy/ofelia.ini` to a `:sha-…` or `:v…` tag for reproducible production runs.
