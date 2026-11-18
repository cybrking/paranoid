---
name: paranoid-gain
description: >
  List the current threat model's identified controls and check status, with
  published benchmark cost as context. One-shot display for /paranoid-gain,
  "paranoid impact", or "what controls did paranoid find".
---

# Paranoid Gain

This is a one-shot, read-only report. Do not change paranoid mode, write files,
or persist a result. If `./threat-model/model.json` exists, run the bundled
standard-library script to count and enumerate its controls and linked checks:

```sh
python3 "<skill-dir>/scripts/control_inventory.py" "threat-model/model.json"
```

For an explicit request for history, changes or one control, use the same script
with `--history --root <repository-root>`, add `--compare` (previous published run)
or `--compare <run-id>`, and `--control <control-id>` when requested. These options
read validated sidecars and recompute current source freshness; they do not run
tests, persist records or repair history. Missing history says `no_history`; a first
run says `no_baseline`. Errors never authorize a fallback success claim. Show the
last recorded outcome separately from `matching`, `stale`, `unknown` or `not_run`
freshness, along with the origin run and rerun reason. Test references are digests;
use the named model check/procedure for context. The original no-option inventory
remains standard-library-only. History mode needs the installed sibling core and
its existing validation dependency. For recording, require the developer's explicit
approved test selection and use `/paranoid-record`; a report request grants no
execution authority.

Resolve `<skill-dir>` to this skill's installed directory. Show the model ID
and snapshot, then **N identified controls; M with written check procedures**,
plus counts of recorded check outcomes. List
every control's ID, requirement, proposed/implemented status, and each check's
recorded outcome (`pass`, `fail`, `blocked`, or `not_run`). A recorded check is
not proof that the control works; call it verified only after checking current
execution evidence and the model validator's closure conditions. If the script
fails, report the error and do not guess a count. This is a current-snapshot
inventory, not a count of controls Paranoid added relative to a baseline.

If there is no current model, show this **published AUTH-77 SSO example**, not
as the current project's result. It produced **7 proposed fix specs with
done-when checks; none of those checks had run**:

1. Prove ownership before linking an existing account (SC-01).
2. Verify a workspace owns a domain before trusting its IdP (SC-02).
3. Reject invalid, misdirected, or replayed SAML responses (SC-03).
4. Scope each SSO session to its workspace (SC-04).
5. End access when IdP or workspace access is removed (SC-05).
6. Give newly provisioned users the lowest role (SC-06).
7. Restrict and audit SSO configuration changes and recovery (SC-07).

Source: `benchmark/published/round1/auth-77/with-paranoid.md`. Link to it in
the installed plugin when available; otherwise name that path as text.

Show the measured cost alongside the controls, labeled as a benchmark average:

```text
  benchmark cost               round 1 · 19 paired cases · Claude Code
                               without → with paranoid
  Cost per run                  $0.232 → $1.055  +$0.823
  Time per run                  61.2s  → 241.7s  +180.5s
  One run per case; these costs are not this task's costs.
```

Source: `benchmark/published/round1/report.md`. Link to it when available.
Round 1 also recorded more invented facts and unbacked done claims with
Paranoid. Do not hide this if discussing benchmark quality. Do not claim a
measured reduction in flaws: planted-flaw discovery and build abuse-test
results were 100% in both conditions. Never estimate a current project's
counterfactual flaws or cost without a measured baseline.
