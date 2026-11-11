# paranoid guide

The details behind the [README](../README.md). What he reads, what he writes, how to check it and how to work on him.

## Inputs

Give him any combination of a pasted idea, a feature request, Jira ticket text or a ticket reference he can read, a design document, or repositories. Optional AWS read access lets him add configuration observations that are in scope. Basic modeling needs no Jira connector, AWS SDK or cloud access. A ticket key alone needs a connector that can read it, or the pasted content. He can't retrieve context he has no access to.

## What you get

Every run writes three linked files to `./threat-model/`.

When one applies, he builds each control to an OWASP ASVS requirement or a CIS Benchmark recommendation. He only cites an ID he read in the source.

| File | What it holds |
| :- | :- |
| `security-controls.md` | Prioritized fix specs with the risk, the fix, where it goes, observable done when checks, an owner and timing |
| `assessment.md` | Scope, assumptions, evidence review, visibility gaps, check results and owner decisions |
| `model.json` | Versioned, machine readable assets, trust boundaries, attack scenarios, controls and checks |

For example, an early tenant export feature could produce this **proposed** requirement, not yet verified.

| Control | Requirement | Enforcement | Acceptance criteria |
| :- | :- | :- | :- |
| Exports scoped to the tenant | Authorize every export against the signed in user's current tenant membership | Request handler, worker data access, status endpoint, download handler | Tenant A cannot request, poll or download tenant B's export. Access revoked before execution or download denies access |

See the fictional [tenant export controls](../examples/tenant-export/security-controls.md) and [AI support controls](../examples/support-assistant/security-controls.md), produced in the [recorded evaluation](non-code-evaluation.md). They are partial, proposed design requirements. Adapt them to your actual scope and evidence.

## Always on mode

The plugin's hooks load his rules into every Claude Code session and every subagent. If your repo has `threat-model/model.json`, its proposed controls for open critical or high priority threats load at session start, as project data rather than instructions. Editing a file the model cites brings one note per session that the model may be stale. The hooks need `python3` on your path and never block a session.

| Level | What he does |
| :- | :- |
| `lite` | Builds what you asked and names the risky part in one line |
| `full` | Builds the safe version by default. This is the starting level |
| `ultra` | Asks who may do what before he builds, and pushes back on anything the need doesn't justify |

Switch with `/paranoid-mode lite`, `full`, `ultra` or `off`. Set `PARANOID_DEFAULT_MODE` to change the starting level.

## Manual install

From a terminal on macOS or Linux:

```sh
git clone --depth 1 https://github.com/cybrking/paranoid.git
mkdir -p ~/.claude/skills
cp -R paranoid/skills/paranoid paranoid/skills/paranoid-ticket paranoid/skills/paranoid-repo paranoid/skills/paranoid-refresh paranoid/skills/paranoid-mode ~/.claude/skills/
```

For Codex, copy `paranoid/skills/paranoid` and `paranoid/skills/paranoid-mode` into `~/.agents/skills/` instead. Copied skills don't get the hooks, so he only steps in when the agent picks up the paranoid-mode skill.

## Validate a model

The validator needs Python 3.10 or later with `jsonschema`, or `uv`, which supplies it. Without them, he says validation was blocked instead of claiming it passed.

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

The CI workflow runs local checks only. It doesn't call paid model APIs, read Jira or connect to AWS. Behavioral evaluations need an authenticated harness and the [evaluation rubric](evaluation.md). See [release readiness](release-readiness.md), [contributing](../CONTRIBUTING.md) and [security reporting](../SECURITY.md).

## Framework and versioning

The [framework](../skills/paranoid/references/framework.md) combines harm first scoping, STRIDE, privacy analysis, attacker capabilities, attack paths, business misuse and testable security requirements. The AI profile applies only when the assessed system contains AI. The [method comparison and primary source attribution](../skills/paranoid/references/comparison.md) explain the synthesis and its tradeoffs. This project doesn't claim ownership of those methods.

Schema 0.2 accepts sources other than code as well as repositories. Models on 0.1 need an explicit migration. Keep the original, review where its inputs came from, change the schema version only after that review, then revalidate relationships and closure claims. A validator version is separate from a schema version.
