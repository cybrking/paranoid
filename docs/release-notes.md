# Unreleased

- README before/after now shows a real round 1 pair, AUTH-77 with and without paranoid, and both outputs are published under `benchmark/published/round1/auth-77/`.
- Always on mode states plainly that a change with no trust boundary gets no `paranoid:` line at all. Round 1 of the benchmark caught him writing "paranoid: no trust boundary here" on a formatting task. One rerun of the no boundary task after the fix stayed quiet, for $0.17.
- Controls can build to named sources. New `references/control-sources.md` says when to use OWASP ASVS for application behavior and CIS Benchmarks for cloud and platform settings, how to cite only IDs read in the source, and how to turn them into done-when checks. Controls in `model.json` take an optional `references` list, with NIST 800-53 and CSF tags for tracking only. The validator reports unchecked IDs and controls with only tracking tags. Schema stays draft 0.2, since the field is optional.
- Shorter README in the style of a one page pitch. The details moved to `docs/guide.md`.
- Benchmark kit in `benchmark/`: 21 cases with sealed answer keys, a runner that starts a fresh Claude Code session per run, hidden abuse tests for always on mode and a blind judge for threat models. No numbers yet.

# paranoid 0.4.0 (always on mode)

- New always on mode. Claude Code hooks load the new `paranoid-mode` rules into every session and every subagent. Before code crosses a trust boundary he builds the safe version, asks one question only when it changes the design, leaves an abuse case test and ends with a `paranoid:` line. He stays silent on changes with no security impact.
- Levels `lite`, `full` and `ultra`, switched with `/paranoid-mode`, or `off`. `PARANOID_DEFAULT_MODE` sets the starting level.
- If the repo has `threat-model/model.json`, its proposed controls for open critical or high priority threats load at session start, as project data rather than instructions.
- Editing a file the model cites as code or config evidence brings one suggestion per session to run `/paranoid-refresh`.
- The hooks are one standard library Python script and never block a session. 14 new tests cover them.

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
