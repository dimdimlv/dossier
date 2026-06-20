# ADR-001: Public/private repository separation for code and personal data

## Status

Accepted — 2026-05-03

## Context

Dossier operates on personally identifiable information (PII) and sensitive professional data: the user's full skill inventory, generated CVs, cover letters, application history with employer names, and API credentials. At the same time, the project has explicit goals as a public learning artifact:

- The code should be shareable, forkable, and visible to potential employers as a portfolio piece.
- The project's development practices (architecture decisions, CI/CD, monitoring) should be observable to demonstrate engineering maturity.
- The user should retain full control over personal data, with strong guarantees against accidental disclosure.

These goals create direct tension with a single-repository layout. Once any PII enters git history of a public repository, removing it is effectively impossible — clones, forks, third-party caches, and archive services preserve it indefinitely. Industry incidents involving leaked credentials in public repos are weekly occurrences, including at companies with mature security practices.

A decision is needed about how code and data are organized at the repository level, and how they communicate at runtime.

## Considered alternatives

### A. Single public repository containing everything

All code and data in one public repo on GitHub.

- **Pros:** simplest possible setup; one place for everything.
- **Cons:** PII permanently exposed; impossible to share code without exposing the user; commits to the inventory create noise in the code history; secret scanning becomes the only defense.
- **Verdict:** rejected. Security and audience-mismatch problems are disqualifying.

### B. Single private repository containing everything

All code and data in one private repo.

- **Pros:** simple; data is protected.
- **Cons:** loses the public-portfolio benefit entirely; collaboration and external review become impossible; the project cannot serve its second goal as a learning artifact for outside readers.
- **Verdict:** rejected. The author has explicitly chosen a public-portfolio dimension for this project.

### C. Two repositories — public for code, private for data

Code lives in a public `dossier` repo. Personal data, secrets, and generated artifacts live in a separate private `dossier-data` repo. The two are physically independent; the running application locates data via an environment variable.

- **Pros:** PII never enters public history; code can be shared, forked, audited; clean separation of change rhythms (code changes by feature work, data changes by life events); aligns with widely adopted patterns (Twelve-Factor App, secrets-out-of-code).
- **Cons:** initial setup is slightly more complex; the user must maintain two repos; risk of accidental cross-contamination if guardrails are not in place.
- **Verdict:** chosen.

## Decision

Adopt a two-repository structure:

- **`dossier`** (public): all source code, schemas, tests, prompt templates, documentation, ADRs, configuration templates (`.env.example`), and synthetic test data.
- **`dossier-data`** (private): the user's real inventory, generated CVs and cover letters, application log database, secrets file (`.env`).

The two repositories are decoupled at runtime via the `DOSSIER_DATA_PATH` environment variable. The application code never contains a hard-coded path to personal data. Tests substitute this path with a temporary directory containing fixtures.

To prevent accidental contamination, we adopt **defense in depth** at three layers:

1. **`.gitignore`** in the public repo, configured from the first commit, excludes patterns that match personal data: `.env`, `data/`, generated CV/letter files, local databases.
2. **Pre-commit hooks** using the `pre-commit` framework with `detect-secrets` (or equivalent) scan staged content for credentials, email patterns, and high-entropy strings before each commit. Commits failing the scan are blocked locally.
3. **GitHub secret scanning** is enabled on the public repository as an additional safety net.

This pattern follows Twelve-Factor App principle III ("Config in environment") and is the standard approach for any application that operates on user data.

## Consequences

### Positive

- Personal data is never exposed in public git history, even by accident, provided guardrails are in place.
- The public repo demonstrates a clean engineering project, suitable for portfolio use and external review.
- The code can be shared, forked, or run by anyone — they bring their own `dossier-data`.
- The setup mirrors a real production pattern (12-factor configuration, secrets management) — practice transferable to professional work.
- Inventory changes do not pollute code history; code changes do not require commits in the data repo.

### Negative

- Initial repo setup is more involved than a single-repo layout.
- The user must keep two repositories in sync conceptually (e.g., when the inventory schema changes, both code and data need coordinated updates).
- A misconfiguration in `.gitignore` or a missing pre-commit hook could still leak data — the defenses must actually be installed, not merely planned.

### Neutral

- Requires environment-variable-based configuration from day one. This is a desirable practice in any case but adds a small upfront learning cost.
- Generated artifacts (CVs, cover letters) consistently land in `dossier-data`, never in `dossier` — this rule must be enforced in code paths that write output.

### Mitigations

- `.gitignore`, `.env.example`, and pre-commit configuration are added in the very first commit, before any real data exists locally.
- A short section in the public README documents the two-repo layout and the contamination risk for future contributors and for the author's future self.
- A periodic review (e.g., before each milestone) audits both repositories for accidental drift.

## References

- Nygard, M. (2011). *Documenting Architecture Decisions.*
- The Twelve-Factor App, factor III: *Config* — https://12factor.net/config
- GitHub docs on secret scanning for public repositories.
