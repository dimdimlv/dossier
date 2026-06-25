# Architecture Decision Records

This directory contains the Architecture Decision Records (ADRs) for Dossier.

An ADR captures a single significant architectural decision: the context in which it was made, the alternatives considered, the decision itself, and its consequences. ADRs are immutable once accepted — if a decision changes, a new ADR is added that supersedes the old one, rather than editing history.

Format follows Michael Nygard's ADR template, extended with an explicit "Considered alternatives" section.

## Index

| # | Title | Status |
|---|-------|--------|
| [001](ADR-001-public-private-data-separation.md) | Public/private repository separation for code and personal data | Accepted |
| [002](ADR-002-mit-license.md) | MIT license for the public code repository | Accepted |
| [003](ADR-003-python-project-layout.md) | Python project layout: src/ + packaged application via uv | Accepted |
| [004](ADR-004-inventory-schema.md) | Inventory schema: hybrid YAML + Markdown frontmatter, validated with Pydantic v2 | Accepted |
| [005](ADR-005-application-tracker-persistence.md) | Application tracker persistence: SQLite via SQLAlchemy 2.0 + Alembic, documents as hashed files | Accepted |
| [006](ADR-006-engine-jd-analysis.md) | Engine: Anthropic SDK + structured outputs, hybrid JD gap analysis | Accepted |
| [007](ADR-007-multi-provider-llm.md) | Multi-provider LLM support: pluggable engine clients (Anthropic default, OpenAI optional) | Accepted |
| [008](ADR-008-cv-generation.md) | CV generation: Jinja2 templating, hybrid deterministic selection + LLM phrasing, draft/frozen separation | Accepted |
| [009](ADR-009-cover-letter-generation.md) | Cover letter generation: composed prose with structured paragraphs and best-effort anti-fabrication | Accepted |
| [010](ADR-010-containerization.md) | Containerization: uv multi-stage Docker image + docker-compose for CLI invocation | Accepted |
| [011](ADR-011-ci-pipeline.md) | Continuous integration with GitHub Actions (lint, type-check, test, secret scan, Docker build) | Accepted |
| [012](ADR-012-deployment.md) | Deployment: image to GHCR, docker-compose on a VPS, scheduled job via Ofelia | Accepted |
| [013](ADR-013-observability.md) | Observability: Prometheus + Grafana with a Pushgateway for the batch CLI | Accepted |

## Status legend

- **Proposed** — under discussion, not yet in effect
- **Accepted** — decided and currently in force
- **Deprecated** — no longer applies, not replaced
- **Superseded by ADR-NNN** — replaced by a later decision
