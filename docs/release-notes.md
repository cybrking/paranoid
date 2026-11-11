# paranoid 0.3.0 (rename and commands)

Threat Model Kit is now **paranoid**. Repository: `cybrking/paranoid` (renamed from `threat-model-kit`; GitHub redirects old links).

- The core skill folder and command are now `skills/paranoid` and `/paranoid` (previously `repo-threat-model`). The threat modeling workflow, references, schema 0.2 and validator 0.2.1 are unchanged.
- New commands: `/paranoid-ticket`, `/paranoid-repo` and `/paranoid-refresh`, each a thin entry point into the same workflow.
- Installable as a Claude Code plugin: `claude plugin marketplace add cybrking/paranoid`.
- Benchmark method published in [benchmark-plan.md](benchmark-plan.md); no benchmark results yet.

The notes below describe the earlier Threat Model Kit alpha.

---

# Public alpha release

Project: **Threat Model Kit**  
Repository: `threat-model-kit`  
Tagline: **From an idea to controls engineering can build and verify.**  
Owner: `cybrking`  
License: [Apache 2.0](../LICENSE)  
Tag: `v0.2.1-alpha.1` (GitHub prerelease; not a stable or production-certified release)

Repository description:

> Threat modeling skill designed for Claude Code and Codex: turn ideas, tickets, designs, and repositories into evidence-grounded models and engineering security controls.

Topics: `threat-modeling`, `agent-skills`, `claude-code`, `codex`, `security`, `application-security`.

## Release description

This experimental skill supports early ideas and feature/Jira text as well as design documents and one or more repositories. Authorized AWS read observations are optional. It produces a machine-readable threat model, an evidence/decision assessment, and prioritized engineering controls with requirements, owners, enforcement points, and negative acceptance criteria.

The framework combines established modeling techniques while preserving assumptions, source provenance, stable IDs, and evidence-backed state transitions. Its validator checks recorded structure and consistency; it cannot establish that evidence is genuine, threats are exhaustive, or controls are effective.

The candidate includes 22 passing automated tests and a portable installation layout. Review the [verification record](verification.md) and [non-code evaluation](non-code-evaluation.md) for exact behavioral results and failures. Authenticated Claude Code testing, live Jira/AWS integration, and representative real-project pilots remain outstanding. GitHub CI passed on Python 3.10 and 3.14; the exact run is linked in the verification record.

This is an alpha released under the [release checklist](release-readiness.md). Do not add passing CI or fully verified harness badges until their checks actually run.
