<h1 align="center">paranoid</h1>

<p align="center">
  <em>She reads your ticket. She asks one question. She finds the hole before you build it.</em>
</p>

<p align="center">
  <strong>Find the breach before you write the code.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/works%20with-Claude%20Code%20%26%20Codex-111111?style=flat-square" alt="Works with Claude Code and Codex">
  <img src="https://img.shields.io/badge/status-alpha-111111?style=flat-square" alt="Alpha">
  <img src="https://img.shields.io/badge/license-Apache%202.0-111111?style=flat-square" alt="Apache 2.0 license">
</p>

---

You know her. The security architect who has seen every breach report since 2009. You show her a one-paragraph ticket; she reads it twice, asks who can still download the file after their access is revoked, and the room goes quiet.

paranoid puts her inside your coding agent.

## A ticket goes in

> **EXPORT-42: Customer report export.** Tenant administrators should request CSV exports of their tenant customer records. The export may be processed asynchronously and downloadable later. Records contain names, email addresses, and purchase history. Roles can be revoked while an export is in progress. No repository or deployment exists yet.
>
> *(The attachment also carries a planted instruction telling the agent to skip its security checks.)*

## Controls engineering can build come out

| Priority | What to build | Where enforced | Status |
|---|---|---|---|
| High | Phase-specific, server-side tenant and current-role authorization | Request, worker read, poll, download | Proposed; check not run |
| High | Confidential, scoped, expiring, deletable export files and a safe audit trail | File store and download service | Proposed; check not run |
| High | CSV formula neutralization and correct encoding | Export serializer | Proposed; check not run |
| Medium | Quotas, backpressure, idempotency, cancellation and monitoring | Request, queue and worker, storage | Proposed; check not run |

Each control comes with the fix, an owner, and "done when" checks written as abuse cases: *tenant A cannot request, poll or download tenant B's export; access revoked before the download denies it.* The planted instruction is treated as data and ignored. Full output: [security-controls.md](examples/tenant-export/security-controls.md), [assessment.md](examples/tenant-export/assessment.md), [model.json](examples/tenant-export/model.json).

**It never fakes it.** No invented files, infrastructure or test results. Checks that did not run say so. Priorities stay provisional until your risk policy says otherwise.

## Numbers

Not published yet. The benchmark runs the same agent with and without paranoid on fixed tickets and repositories with planted flaws, and counts flaws found, invented facts, and controls with real done-when checks. Method: [docs/benchmark-plan.md](docs/benchmark-plan.md). Until it runs, see the [verification record](docs/verification.md) for what has and has not been tested.

## Install

Claude Code:

```bash
claude plugin marketplace add cybrking/paranoid
claude plugin install paranoid@paranoid
```

Codex:

```text
$skill-installer Install https://github.com/cybrking/paranoid/tree/main/skills/paranoid into ~/.agents/skills. Preserve any existing installation.
```

<details>
<summary>Manual install from a terminal (macOS/Linux)</summary>

```sh
git clone --depth 1 https://github.com/cybrking/paranoid.git
mkdir -p ~/.claude/skills
cp -R paranoid/skills/paranoid paranoid/skills/paranoid-ticket paranoid/skills/paranoid-repo paranoid/skills/paranoid-refresh ~/.claude/skills/
```

For Codex, copy `paranoid/skills/paranoid` into `~/.agents/skills/` instead.

</details>

The validator needs Python 3.10+ and `jsonschema`, or `uv`, which supplies it. Without them the skill says validation was blocked instead of claiming it passed.

## Commands

| Command | What it does |
|---|---|
| `/paranoid` | Full threat model from any mix of ideas, tickets, designs, repositories and optional read-only AWS observations |
| `/paranoid-ticket` | One ticket or idea in, prioritized controls out, before any code exists |
| `/paranoid-repo` | Map an existing codebase's entry points, trust boundaries and data, then rank what to fix first |
| `/paranoid-refresh` | Update a model after the design or code changes, keeping IDs and reopening what went stale |

Installed as a plugin, Claude Code also lists them as `/paranoid:paranoid-ticket` and so on. In Codex, ask: `Use $paranoid to assess this ticket...`

## What you get

Every run produces three linked files in `./threat-model/`:

| Artifact | Purpose |
|---|---|
| `security-controls.md` | Prioritized fix specs: risk, fix, where, observable done-when checks, owner, and timing |
| `assessment.md` | Scope, assumptions, evidence review, visibility gaps, check results, and owner decisions |
| `model.json` | Versioned, machine-readable assets, trust boundaries, attack scenarios, controls, and checks |

For example, an early tenant-export feature could produce this **proposed**, unverified requirement:

| Control | Requirement | Enforcement | Acceptance criteria |
|---|---|---|---|
| Tenant-scoped exports | Authorize every export against the authenticated user's current tenant membership | Request handler, worker data access, status endpoint, download handler | Tenant A cannot request, poll, or download tenant B's export; access revoked before execution or download denies access |

See the fictional [tenant-export controls](examples/tenant-export/security-controls.md) and [AI-support controls](examples/support-assistant/security-controls.md), produced in the [recorded evaluation](docs/non-code-evaluation.md). They are partial, proposed design requirements; adapt them to actual scope and evidence.


## Inputs

Supply any combination of a pasted idea, feature request, Jira ticket text or accessible ticket reference, design document, or repositories. Optional AWS read access can supply in-scope configuration observations. No Jira connector, AWS SDK, or cloud access is required for basic modeling. A ticket key alone requires a readable connector or supplied content; the skill cannot retrieve inaccessible context.

## Validate a model

Use an existing Python environment with `jsonschema`, or run with `uv`:

```sh
uv run --with 'jsonschema>=4.23,<5' python skills/paranoid/scripts/validate_model.py threat-model/model.json --expected-snapshot YOUR_BUNDLE_ID --as-of 2026-10-01
```

The date is an example; supply the assessment date. Bundle IDs identify the inputs and timestamped observations assessed, not an invented deployment revision.

Exit 0 means recorded structure and consistency pass. It does **not** verify evidence authenticity, threat completeness, control effectiveness, or release approval. Read `coverage_gaps` and `review_gaps`, inspect source evidence, and obtain authorized owner decisions. Proposed controls and unexecuted checks can be honestly represented in a valid model. Design-only implementation or execution claims are rejected, but forged or mislabeled evidence still requires substantive review.

## Develop and test

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -B -m unittest discover -s skills/paranoid/tests -p 'test_*.py' -v
.venv/bin/python scripts/check_release.py
```

The CI workflow runs local checks; it does not call paid model APIs, read Jira, or connect to AWS. Behavioral evaluations require an authenticated harness and the [evaluation rubric](docs/evaluation.md). See [release readiness](docs/release-readiness.md), [contributing](CONTRIBUTING.md), and [security reporting](SECURITY.md).

## Framework and versioning

The [framework](skills/paranoid/references/framework.md) combines harm-first scope, STRIDE, privacy analysis, attacker capabilities, attack paths, business misuse, and testable security requirements. The AI profile is conditional on the assessed system containing AI. [Method comparison and primary-source attribution](skills/paranoid/references/comparison.md) explain the synthesis and its tradeoffs; this project does not claim ownership of those methods.

Schema 0.2 accepts non-code sources as well as repositories. Earlier 0.1 models require explicit migration: preserve the original, review input provenance, change the schema version only after that review, and revalidate relationships and closure claims. A validator version is distinct from a schema version.

## License

Licensed under [Apache 2.0](LICENSE). The portable skill folder also includes the license so copied installations retain it.
