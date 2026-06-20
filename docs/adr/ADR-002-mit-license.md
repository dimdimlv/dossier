# ADR-002: MIT license for the public code repository

## Status

Accepted — 2026-06-20

## Context

The public `dossier` repository is intended to serve as a portfolio piece, a learning artifact, and code that others may freely read, fork, and run (bringing their own `dossier-data`). For any of these to be legally possible, the repository needs an explicit license.

A point that is frequently misunderstood: code published without a license is not "free" code — it is maximally restricted. Under default copyright law, absent an explicit license, no one has the right to use, copy, or modify the work. Public visibility on GitHub does not grant usage rights. Therefore an explicit license is required from the first commit, not as a later addition: any commits made before a license exists leave the rights status of that code ambiguous for anyone who clones or forks in that window.

A license decision is needed before the repository's first commit.

## Considered alternatives

### A. MIT

A short, permissive license: use, copy, modify, and distribute freely, provided the copyright notice is retained; no warranty.

- **Pros:** simplest and most widely recognized permissive license; maximal freedom of use; reassures readers and employers that the code is safe to examine and reuse; no friction.
- **Cons:** contains no explicit patent grant (not a meaningful concern for this project).
- **Verdict:** chosen.

### B. Apache 2.0

Permissive, like MIT, but longer and with an explicit patent grant and patent-litigation protection.

- **Pros:** same freedoms as MIT plus patent clarity; favored by larger and corporate-backed projects.
- **Cons:** longer and more bureaucratic; patent protection is disproportionate for a personal CV-generation tool with no patentable subject matter or corporate contributors.
- **Verdict:** rejected as unnecessary overhead for this project's goals.

### C. GPL v3

A copyleft license requiring derivative works that are distributed to also be released under the GPL.

- **Pros:** guarantees the code and its derivatives remain open.
- **Cons:** the "viral" copyleft requirement discourages commercial reuse and adds friction without benefit for a portfolio project; the author has no requirement that derivatives stay open.
- **Verdict:** rejected. Copyleft solves a problem this project does not have.

## Decision

License the public `dossier` repository under the **MIT License**.

A `LICENSE` file containing the full MIT license text, with the author's name and the current year in the copyright line, is placed in the repository root as part of the first commit. The README references the license and links to the file.

The private `dossier-data` repository is not licensed for distribution — it contains personal data, is not intended to be shared, and remains under default all-rights-reserved copyright by virtue of having no license.

## Consequences

### Positive

- The code is legally safe for others (and the author's future self) to read, fork, and reuse.
- MIT is instantly recognizable; it removes any "am I allowed to use this?" hesitation for visitors and employers.
- Minimal text, zero ongoing maintenance burden.
- Consistent with the dominant convention for personal projects and a large share of the open-source ecosystem.

### Negative

- No explicit patent protection. Accepted as irrelevant for this project.
- Permissive licensing means anyone could, in principle, incorporate the code into a closed-source product. This is an acceptable outcome for a portfolio tool.

### Neutral

- The choice is effectively irreversible for code already published under it (prior commits remain MIT-licensed forever), but the project can adopt a different license for future versions if its goals ever change.
- GitHub detects the license from the `LICENSE` file in the repository root and surfaces it in the repo UI; the file's presence — not a textual mention in the README — is what makes the license effective.

## References

- The MIT License — https://opensource.org/license/mit
- GitHub docs: *Licensing a repository* — https://docs.github.com/articles/licensing-a-repository
- choosealicense.com — comparison of common open-source licenses.
