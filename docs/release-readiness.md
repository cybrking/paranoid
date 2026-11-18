# Release readiness

## Local control-evidence implementation — 2026-11-18

The approved local control history, explicit unittest/JUnit recorder, read-only comparison/control views and fail → pass → stale walkthrough are implemented. Model schema 0.2 remains unchanged; execution history uses sidecar format 1. The shared workflow collects core/gain/record tests on Linux Python 3.10/3.14 and macOS 3.14, with a separate checksum-pinned real Gradle producer job.

The isolated PR candidate collected 84 shared tests locally: 83 passed and the real Gradle case explicitly skipped pending its required hosted job. All 10 baseline benchmark tests, 21 case keys and the license/package gate passed. Earlier implementation checks also exercised the real Gradle producer on Python 3.10 and 3.14 in the original working tree. The [verification record](control-evidence-verification.md) separates those observations from this branch's exact checks. No new runtime dependency was introduced.

Publication and hosted checks are tracked in the PR verification note. Fresh authenticated harness behavior, independent real-project outcomes and production assurance remain open. The historical record below retains its original scope; it does not clear these gates.

## Historical release record

Approved project name: **Threat Model Kit**. Approved GitHub repository: **threat-model-kit**. Keep the portable installed command `repo-threat-model` for compatibility. The descriptive name received a limited collision search; the selected GitHub destination was checked before creation; trademark clearance is not established.

Before public alpha publication:

- Owner `cybrking`, repository `threat-model-kit`, and Apache 2.0 were approved on 2026-10-01. LICENSE is included at the repository and portable-skill roots.
- Review the exact candidate file list and content; publish only this isolated tree.
- Pass local regression, CLI, format, relative-reference, and extracted-package checks. Run `python scripts/check_release.py --require-license` before publication.
- Review the behavioral evaluation evidence and describe untested harness paths honestly.
- Enable private vulnerability reporting or supply an appropriate private route.
- Create the repository and run its CI; a prepared workflow is not evidence that GitHub CI has run.
- Tag an alpha release only after these checks, with a release description listing known limitations.

Before describing harness support as verified: run the latest packaged entrypoint through both authenticated harnesses using repo and non-code inputs, independently validate all outputs, and review engineering handoff quality. Claude authentication has previously blocked this work.

Before production claims: run representative web/API, privacy-sensitive, and AI/tool-system pilots, measure actionable findings and false/missed findings, verify lifecycle updates and scoped AWS observation behavior, and demonstrate remediation outcomes. Alpha publication does not meet those production criteria.

The [release notes](release-notes.md) supply the approved repository metadata and alpha announcement text.

## Completed publication checks — 2026-10-01

- User approved `cybrking/threat-model-kit`, Apache 2.0, and public alpha publication.
- Isolated release tree and fictional examples reviewed; no unrelated workspace contents published.
- All 22 local tests, skill-format validation, and the license/package/example checks passed.
- Public repository created; Apache license detected by GitHub; private vulnerability reporting enabled and verified.
- Source pushed to main; [GitHub validation](https://github.com/cybrking/threat-model-kit/actions/runs/36959526490) passed on Python 3.10 and 3.14.
- Alpha tagging follows a passing validation result for the final release commit.

The remaining harness, cloud, and production gates above are still outstanding; publication does not complete them.
