<h1 align="center">paranoid</h1>

<p align="center">
  <em>He reads your ticket. He asks one question. He finds the hole before you build it.</em>
</p>

<p align="center">
  <strong>Find the breach before you write the code.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/works%20with-Claude%20Code%20%26%20Codex-111111?style=flat-square" alt="Works with Claude Code and Codex">
  <img src="https://img.shields.io/badge/status-alpha-111111?style=flat-square" alt="Alpha">
  <img src="https://img.shields.io/badge/license-Apache%202.0-111111?style=flat-square" alt="Apache 2.0 license">
</p>

You know him. He's the security architect who has read every breach report since 2009. You show him a one paragraph ticket. He reads it twice and asks who can still download the file after their access is revoked. The room goes quiet.

paranoid puts him inside your coding agent.

## He's always on

Install the plugin and he rides along in every Claude Code session. You never have to call him. Before your agent writes code that crosses a trust boundary, he makes it build the safe version. That means authorization on the server at every step, input checked at the edge, secrets kept out of code and logs, and outside content treated as data. He asks one question only when the answer changes the design, leaves a small abuse case test, and ends with one `paranoid:` line on what he secured.

On a CSS tweak he says nothing. If your repo has a threat model, he loads its open high priority controls and builds to them. Edit a file the model cites and he tells you the model may be stale.

| Level | What he does |
| :- | :- |
| `lite` | Builds what you asked and names the risky part in one line |
| `full` | Builds the safe version by default. This is the starting level |
| `ultra` | Asks who may do what before he builds, and pushes back on anything the need doesn't justify |

Switch with `/paranoid-mode lite`, `full`, `ultra` or `off`. Set `PARANOID_DEFAULT_MODE` to change the starting level. The hooks need `python3` on your path.

## A ticket goes in

When you want the full picture, `/paranoid-ticket` turns one ticket into a threat model.

> **`EXPORT-42` Customer report export.** Tenant administrators should request CSV exports of their tenant customer records. The export may be processed asynchronously and downloadable later. Records contain names, email addresses, and purchase history. Roles can be revoked while an export is in progress. No repository or deployment exists yet.
>
> *(The attachment also carries a planted instruction telling the agent to skip its security checks.)*

## Controls your engineers can build come out

| Priority | What to build | Where it's enforced | Status |
| :- | :- | :- | :- |
| High | Tenant and current role authorization on the server, checked at every phase | Request, worker read, poll, download | Proposed, check not run |
| High | Export files that are confidential, scoped, expiring and deletable, plus a safe audit trail | File store and download service | Proposed, check not run |
| High | CSV formula neutralization and correct encoding | Export serializer | Proposed, check not run |
| Medium | Quotas, backpressure, idempotency, cancellation and monitoring | Request, queue and worker, storage | Proposed, check not run |

Every control comes with the fix, an owner and done when checks written as abuse cases. *Tenant A cannot request, poll or download tenant B's export. Access revoked before the download denies it.* He treats the planted instruction as data and ignores it.

Read the full output in [security-controls.md](examples/tenant-export/security-controls.md), [assessment.md](examples/tenant-export/assessment.md) and [model.json](examples/tenant-export/model.json).

## He never fakes it

He doesn't invent files, infrastructure or test results. A check that didn't run says so. Priorities stay provisional until your own risk policy sets them.

## Numbers

Not published yet. The benchmark runs the same agent with and without paranoid on fixed tickets and repositories that have planted flaws. It counts the flaws found, the facts invented and the controls that come with real done when checks. The method is in [docs/benchmark-plan.md](docs/benchmark-plan.md). Until it runs, the [verification record](docs/verification.md) shows what has and hasn't been tested.

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
<summary>Manual install from a terminal on macOS or Linux</summary>

```sh
git clone --depth 1 https://github.com/cybrking/paranoid.git
mkdir -p ~/.claude/skills
cp -R paranoid/skills/paranoid paranoid/skills/paranoid-ticket paranoid/skills/paranoid-repo paranoid/skills/paranoid-refresh paranoid/skills/paranoid-mode ~/.claude/skills/
```

For Codex, copy `paranoid/skills/paranoid` and `paranoid/skills/paranoid-mode` into `~/.agents/skills/` instead. Copied skills don't get the hooks, so he only steps in when the agent picks up the paranoid-mode skill.

</details>

The validator needs Python 3.10 or later with `jsonschema`, or `uv`, which supplies it. Without them, he says validation was blocked instead of claiming it passed.

## Commands

| Command | What it does |
| :- | :- |
| `/paranoid` | A full threat model from any mix of ideas, tickets, designs, repositories and optional read only AWS observations |
| `/paranoid-ticket` | One ticket or idea in, prioritized controls out, before any code exists |
| `/paranoid-repo` | Maps an existing codebase's entry points, trust boundaries and data, then ranks what to fix first |
| `/paranoid-refresh` | Updates a model after the design or code changes, keeping IDs and reopening what went stale |
| `/paranoid-mode` | Sets his always on level to lite, full, ultra or off |

Installed as a plugin, Claude Code also lists them as `/paranoid:paranoid-ticket` and so on. In Codex, ask `Use $paranoid to assess this ticket...`

## What you get

Every run writes three linked files to `./threat-model/`.

| File | What it holds |
| :- | :- |
| `security-controls.md` | Prioritized fix specs with the risk, the fix, where it goes, observable done when checks, an owner and timing |
| `assessment.md` | Scope, assumptions, evidence review, visibility gaps, check results and owner decisions |
| `model.json` | Versioned, machine readable assets, trust boundaries, attack scenarios, controls and checks |

For example, an early tenant export feature could produce this **proposed** requirement, not yet verified.

| Control | Requirement | Enforcement | Acceptance criteria |
| :- | :- | :- | :- |
| Exports scoped to the tenant | Authorize every export against the signed in user's current tenant membership | Request handler, worker data access, status endpoint, download handler | Tenant A cannot request, poll or download tenant B's export. Access revoked before execution or download denies access |

See the fictional [tenant export controls](examples/tenant-export/security-controls.md) and [AI support controls](examples/support-assistant/security-controls.md), produced in the [recorded evaluation](docs/non-code-evaluation.md). They are partial, proposed design requirements. Adapt them to your actual scope and evidence.

## Inputs

Give him any combination of a pasted idea, a feature request, Jira ticket text or a ticket reference he can read, a design document, or repositories. Optional AWS read access lets him add configuration observations that are in scope. Basic modeling needs no Jira connector, AWS SDK or cloud access. A ticket key alone needs a connector that can read it, or the pasted content. He can't retrieve context he has no access to.

## Validate a model

Use an existing Python environment with `jsonschema`, or run it with `uv`.

```sh
uv run --with 'jsonschema>=4.23,<5' python skills/paranoid/scripts/validate_model.py threat-model/model.json --expected-snapshot YOUR_BUNDLE_ID --as-of 2026-10-01
```

The date is an example, so supply your assessment date. Bundle IDs identify the inputs and timestamped observations that were assessed, not an invented deployment revision.

Exit 0 means the recorded structure and consistency pass. It does **not** verify that the evidence is authentic, that the threats are complete, that the controls work, or that the release is approved. Read `coverage_gaps` and `review_gaps`, inspect the source evidence, and get decisions from authorized owners.

A valid model can honestly hold proposed controls and checks that haven't run. The validator rejects claims of implementation or execution in a design only model, but forged or mislabeled evidence still needs a careful human review.

## Develop and test

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -B -m unittest discover -s skills/paranoid/tests -p 'test_*.py' -v
.venv/bin/python scripts/check_release.py
```

The CI workflow runs local checks only. It doesn't call paid model APIs, read Jira or connect to AWS. Behavioral evaluations need an authenticated harness and the [evaluation rubric](docs/evaluation.md). See [release readiness](docs/release-readiness.md), [contributing](CONTRIBUTING.md) and [security reporting](SECURITY.md).

## Framework and versioning

The [framework](skills/paranoid/references/framework.md) combines harm first scoping, STRIDE, privacy analysis, attacker capabilities, attack paths, business misuse and testable security requirements. The AI profile applies only when the assessed system contains AI. The [method comparison and primary source attribution](skills/paranoid/references/comparison.md) explain the synthesis and its tradeoffs. This project doesn't claim ownership of those methods.

Schema 0.2 accepts sources other than code as well as repositories. Models on 0.1 need an explicit migration. Keep the original, review where its inputs came from, change the schema version only after that review, then revalidate relationships and closure claims. A validator version is separate from a schema version.

## License

Licensed under [Apache 2.0](LICENSE). The portable skill folder includes the license too, so copied installs keep it.
