# Control-evidence verification — 2026-11-18

The PR branch `codex/control-evidence-history` is isolated from unrelated local plugin, benchmark, artwork and hook changes, based on `46314ac2982f0bdd69c99923ff46ffd30117b313`. The implementation preserves model schema 0.2 and adds history sidecar format 1; no runtime dependency was added. Pytest is a development-only producer dependency.

## Isolated PR candidate checks

On macOS Python 3.14.10 / Expat 2.7.4, the exact PR candidate collected 59 core, 1 gain and 23 recorder tests: 83 total, 82 passed and one explicit local Gradle skip, in 8.272 seconds. Native/pytest producers, the repeated walkthrough, publication regressions and extracted-package checks passed. The unchanged baseline benchmark suite passed all 10 tests, all 21 case keys passed, and the license/package gate plus `git diff --check` passed. The shared workflow provides a dedicated required Gradle job; hosted results and tested head/merge SHAs are recorded in the PR verification note after publication.

Two unrelated hook tests and twelve unrelated Codex benchmark tests from the earlier working tree are deliberately absent from this branch. That explains the lower counts relative to the initial implementation checks below; none of the control-evidence regressions were omitted.

## Initial implementation checks

The following results were observed before PR isolation in the original dirty working tree. They verify the implemented code and prepared producer tools, but are not exact PR-commit or hosted evidence. In particular, the isolated Codex install below included pre-existing local plugin manifests absent from this PR.

| Check | Observed result |
| --- | --- |
| Shared core/gain/record suite, macOS Python 3.14.10 / Expat 2.7.4 | 85 tests passed, zero skips, 20.448 seconds; positive collection: 61 core, 1 legacy gain, 23 recorder |
| Same suite, macOS Python 3.10.22 / Expat 2.9.0 | 85 tests passed, zero skips, 18.862 seconds |
| Real native unittest and pytest 9.2.0 producers | Passed within both shared runs; actual assertions, skipped/error/incomplete selection and fresh report destinations exercised |
| Real Gradle 9.9.1 / Temurin 21.0.13+9 producer | Passed within both shared runs: pass, repeated pass, then actual authorization assertion failure; three committed matching-input records |
| Disposable walkthrough | Actual fail → pass → stale lifecycle passed twice per shared run, with exactly two retained runs and temporary-repository cleanup |
| Publication and privacy regressions | Conflicting independent writers, corrupt parent, pre/post-HEAD failures, uncertain cleanup, input changes/unavailability, bounded hostile XML and digested test identities passed |
| Extracted package | Sibling core/gain/record copied to a path with spaces; native recording and read-only history passed. Legacy partial-model inventory worked without validation packages; missing core could not fall back to an ambient module. Reads produced no bytecode files. |
| `python -B scripts/check_release.py --require-license` | Passed: metadata, sidecar/model schemas, manual-only recorder metadata, relative links, example models and input digests |
| `python -B -m unittest discover -s benchmark/tests -p 'test_*.py' -v` | 22 tests passed |
| `python -B benchmark/check_keys.py` | 21 cases, zero failed; recorder/walkthrough have no answer-key dependency |
| Isolated Codex local marketplace/install | Accepted `paranoid@paranoid` 0.4.0; installed package contained the recorder, core and schema. No authenticated behavioral session was run. |
| `claude plugin validate` | Passed and listed `paranoid-record`; reported the existing missing listing-icon warning. This command does not run the directory safety/policy review or prove runtime hook behavior. |
| `git diff --check` | Passed |

Gradle and the JDK were downloaded into temporary storage and checksum-verified before execution. No global toolchain or startup configuration was changed. A sandboxed Gradle attempt failed because its local build-lock socket was denied; the unrestricted local reruns above passed without weakening a product check. The earlier partial runs are not counted as final successes.

## Reproduce the shared suite

Install `requirements-dev.txt` into an isolated supported Python environment. For the real Gradle case, provide the pinned Gradle binary as `PARANOID_GRADLE`, its prepared cache as `GRADLE_USER_HOME`, a compatible `JAVA_HOME`, and `PARANOID_REQUIRE_GRADLE=1`. The fixture verifies dependencies before the recorded offline executions.

```sh
python -B - <<'PY'
import unittest
suites = unittest.TestSuite()
for directory in ('skills/paranoid/tests', 'skills/paranoid-gain/tests', 'skills/paranoid-record/tests'):
    suite = unittest.TestLoader().discover(directory, pattern='test_*.py')
    if suite.countTestCases() == 0:
        raise SystemExit('No tests collected: ' + directory)
    suites.addTests(suite)
result = unittest.TextTestRunner(verbosity=2).run(suites)
raise SystemExit(not result.wasSuccessful())
PY
python -B scripts/check_release.py --require-license
python -B benchmark/check_keys.py
python -B -m unittest discover -s benchmark/tests -p 'test_*.py' -v
```

Without `PARANOID_GRADLE`, local discovery explicitly skips that integration. CI's separate producer job requires it and fails when unavailable. The shared workflow also requires positive collection, retains the existing package/benchmark gates, and configures Linux Python 3.10/3.14 plus macOS 3.14. Hosted execution of this working tree has not occurred.

## Regression development evidence

Tests were run failing before implementation/fixes, then rerun passing. Initial history/recorder/release tests failed because the new modules, CLI and package gate did not exist. Later focused failures demonstrated these behaviors:

- Cumulative-history tests require unselected checks to retain their original observation. A later regression exposed a missing comparison for newly observed checks; it now reports `not_run` → `pass`.
- Missing/deleted inputs, forged input digests and publication cleanup errors needed explicit conservative handling; uncertainty now remains visible without rewriting old records.
- Read-only CLI imports created bytecode files; history commands now suppress that write and test the extracted package without relying on `-B`.
- A skipped unittest subtest could leave its owning method green; native callbacks now aggregate onto the method.
- A successfully exited process leader could leave an owned descendant running; a FIFO-handshake regression now verifies cancellation after normal completion as well as timeout handling.
- A changed HEAD digest after bundle preparation could escape the locked parent check; publication now verifies both the prepared parent digest and bounded parent bytes under the lock.
- A source change during reading, or a failed confirmation capture after an initially matching capture, could misstate freshness; both regressions now require an unavailable/changing input identity to stay nonmatching.

The last defect was demonstrated by this focused command returning `matching` instead of `unknown`, then passing after the shared reader fix:

```sh
python -B -m unittest discover -s skills/paranoid/tests -p test_control_history.py -k failed_confirmation -v
```

An independent implementation security review identified the process-descendant and locked-parent defects and verified their fixes. This is bounded code review and regression evidence, not an external audit. Coverage percentages were not measured or used as a release claim.

## Limits

The initial implementation checks preceded PR publication; consult the PR verification note for current hosted results. Fresh authenticated Claude/Codex workflow evaluations, real-project pilots and measured security improvement remain unverified. Native recording relies on local POSIX process groups; it is not a sandbox. History is local same-user evidence, without signatures or protection against a writer who can alter the project and its records. Freshness covers declared inputs, not external services or changes restored between captures. See [usage and trust limits](control-evidence.md).
