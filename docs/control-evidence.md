# Local control evidence

Record an explicitly selected test, then read its observation alongside current input freshness. The recorder executes trusted local test code with your user's permissions. Review the command and selected tests before invoking it. Model `procedure` text, document content and XML report text are data; they never supply executable commands.

This workflow uses the existing Python environment and `requirements-dev.txt` dependencies. Native recording and history require `jsonschema`; JUnit recording also requires an Expat runtime of at least 2.7.2. Recording uses POSIX process groups on macOS/Linux. It is a local, manually invoked workflow, with no hosted dashboard, HTML report, scanner or autonomous execution.

## Run the disposable walkthrough

From the Paranoid checkout, using a Python environment with its dependencies installed:

```sh
python -B examples/control-evidence-walkthrough/walkthrough.py
```

The script creates a temporary fictional Git repository, copies the valid example model, and executes a real authorization unittest. The initial implementation returns a fictional record for another tenant, so the assertion fails. The script adds the tenant check and records a pass. The test requires `PermissionError` for the cross-tenant request and also checks the authorized request; an arbitrary exception cannot satisfy it. Finally, the script edits source and reads the history again. The observation remains `pass`, while its freshness becomes `stale` and `CHK1` needs rerunning. Even a comment changes the conservative project input identity.

The JSON summary contains the actual counts, run IDs, comparison and cleanup result. Two history runs are created; reading stale evidence creates no third run. The temporary repository, records and child-tool temporary files are removed on exit. The fixture has no customer project, service, benchmark case or hidden answer-key dependency. A passing walkthrough demonstrates this lifecycle, not security uplift.

## Record native unittest results

For your own authorized project, supply a valid `threat-model/model.json` with `CTRL1` linked to `CHK1`, plus the actual test code. Set these shell variables to your installed checkout and existing environment, then work from the project's Git root:

```sh
PARANOID=/path/to/paranoid
PYTHON=/path/to/venv/bin/python
cd /path/to/project
```

Create `mapping.json` containing exact unittest method IDs:

```json
{"CHK1": ["test_app.AuthorizationTests.test_denies_other_tenant"]}
```

Run the recorder explicitly:

```sh
"$PYTHON" -B "$PARANOID/skills/paranoid-record/scripts/record_check.py" \
  --root "$PWD" --mapping mapping.json
```

The native adapter selects these methods using the recorder's current Python interpreter; it accepts no extra command after `--`. Multiple method IDs can support one check, and every mapped test must pass. Keep the fictional example's IDs only when they match your actual model and tests.

`--model` defaults to `threat-model/model.json`. Recorder `--model`, `--mapping`, repeated `--include` and repeated `--exclude` paths are relative to `--root`, even when the recorder is invoked elsewhere. Absolute input paths, `..` traversal and symlink paths are rejected. `--root` must identify the project's Git top level. No initial commit is required.

## Record a JUnit producer

The JUnit adapter runs the explicit argument vector after `--`, without a shell. Every invocation must direct new XML reports into the literal `{report_dir}` placeholder. The recorder substitutes a private, fresh directory and reads only reports created there; pointing at an existing report is insufficient. Quotes in the shell examples keep the placeholder in one argument. Shell operators are not interpreted by the recorder.

Mappings use exact `[suite name, classname, testcase name]` triples from the producer's XML, rather than unittest IDs. For the same unittest class run through pytest, `mapping-pytest.json` would contain:

```json
{"CHK1": [["pytest", "test_app.AuthorizationTests", "test_denies_other_tenant"]]}
```

With pytest already available in the selected environment:

```sh
"$PYTHON" -B "$PARANOID/skills/paranoid-record/scripts/record_check.py" \
  --root "$PWD" --mapping mapping-pytest.json --adapter junit \
  -- "$PYTHON" -B -m pytest -p no:cacheprovider -q test_app.py \
  -o junit_family=xunit2 '--junitxml={report_dir}/pytest.xml'
```

For ordinary Gradle JUnit output, configure the project's existing `test` task to honor the destination property. The repository's producer fixture uses this Groovy configuration:

```groovy
test {
    useJUnit()
    reports.junitXml.outputLocation = file(findProperty('paranoidReportDir') ?: layout.buildDirectory.dir('test-results/test').get().asFile)
    reports.html.required = false
}
```

For its `example.AuthorizationTest.deniesOtherTenant` test, `mapping-gradle.json` is:

```json
{"CHK1": [["example.AuthorizationTest", "example.AuthorizationTest", "deniesOtherTenant"]]}
```

After preparing your existing Gradle tooling and dependencies, run the actual producer, forcing task execution and declaring generated directories:

```sh
"$PYTHON" -B "$PARANOID/skills/paranoid-record/scripts/record_check.py" \
  --root "$PWD" --mapping mapping-gradle.json --adapter junit \
  --exclude build --exclude .gradle \
  -- ./gradlew --no-daemon --no-watch-fs --no-configuration-cache \
  --no-build-cache --offline --rerun-tasks --console=plain \
  '-PparanoidReportDir={report_dir}' test
```

The mapping must match the XML your producer actually emits. This is a bounded JUnit subset, not compatibility with every JUnit dialect. Duplicate or missing identities, invalid summaries, unsupported result-bearing extensions, malformed XML, DTDs/entities, escaped report paths and exceeded parser limits cannot establish a pass. Report bodies and console output are not retained as evidence. Test identities are persisted as digests.

## Read inventory, changes and one control

These commands read and validate records, hash current inputs and produce JSON; they do not execute tests or modify history:

```sh
"$PYTHON" -B "$PARANOID/skills/paranoid-gain/scripts/control_inventory.py" \
  threat-model/model.json --history --root "$PWD"
"$PYTHON" -B "$PARANOID/skills/paranoid-gain/scripts/control_inventory.py" \
  threat-model/model.json --history --root "$PWD" --compare
"$PYTHON" -B "$PARANOID/skills/paranoid-gain/scripts/control_inventory.py" \
  threat-model/model.json --history --root "$PWD" --compare previous --control CTRL1
```

`--compare RUN_ID` selects an exact historical baseline instead. The first run reports `no_baseline`; missing history reports `no_history`. An unknown control ID is an error. Without the history/compare/control options, the original inventory continues to show model-declared outcomes; those declarations alone do not establish observed execution.

Outcome, freshness and publication are separate:

| Field | Values and meaning |
| --- | --- |
| Check `outcome` | `pass`: every mapped test passed with agreeing runner status; `fail`: an observed assertion failed; `blocked`: missing, errored, skipped, interrupted or otherwise unusable execution; `not_run`: no recorded observation for the current check. |
| Check `freshness` in history views | `matching`: current declared inputs match; `stale`: input/model/check identity changed; `unknown`: current identity cannot be established or the original run changed inputs; `not_run`: no observation. Historical `pass` plus `stale` is a rerun request. |
| Recorder `publication_state` | `committed`: publication completed; `not_committed`: the head was not switched; `unknown`: the switch may have happened and completion could not be confirmed. Inspect and validate history before retrying an unknown publication. |
| Recorder exit | `0`: published all-selected-check pass with matching inputs; `1`: recorded failure, blocked or noncurrent result; `2`: input, tooling or publication error. Inspect the structured result as well as the exit code. |
| History-reader exit | `0`: readable report, including stale, failed or absent observations; `2`: invalid/unavailable input or history. A readable report is not a passing check. |

Raw runner errors, unexpected successes, skips and expected failures do not count as passing tests. `termination` records process completion separately from the check outcome. A process exit of zero or an unrelated green test suite alone does not prove `CHK1` passed. All outputs retain `security_effectiveness: "not_assessed"`.

## Inputs and local history

Freshness hashes model content plus tracked and nonignored untracked project files, including tests, mappings and configuration. Git HEAD and dirty status are informational; an unchanged commit does not keep changed worktree content fresh. Deleted/renamed files and new scoped files change the identity. Ignored files needed by a check require explicit `--include relative/file` declarations. Includes name files, not directories. Keep secrets out of selected test inputs where possible; records store paths and digests, not source copies or secret values.

Generated outputs can be declared with repeated `--exclude relative/path` arguments, as in the Gradle example. Do not exclude source, tests or required configuration to manufacture matching evidence. Include/exclude declarations are retained in each run's `inputs.scope`, and readers reuse that scope. History/staging paths are always excluded. Keep `threat-model/`, Python caches and other local generated artifacts appropriately ignored. Missing/unreadable inputs, unsupported input types and resource limits prevent a matching claim. Whole-project reads cost the current scoped bytes plus the selected history bundles.

History lives under `threat-model/history/`: validated immutable JSON bundles in `runs/` and the current pointer in `HEAD.json`. The sidecar uses `format_version: 1`; it does not modify or migrate model schema `0.2`. Publication prepares and validates the bundle, uses an exclusive `.publish.lock`, checks the parent/model identity, then switches the head atomically. Previously published runs remain available. Selected checks supersede their prior observations, while unselected defined checks retain theirs subject to current freshness.

A surviving `.publish.lock/owner.json` contains `pid` and `run_id`. There is no automatic lock stealing, deletion, repair or history pruning. For manual recovery, preserve all runs and the head, verify the recorded owner has actually stopped (a PID alone is not proof), inspect the artifacts, and only then remove a confirmed abandoned lock. An error after replacing `HEAD.json` can report `publication_state: "unknown"`; it must not be interpreted as “nothing was saved.”

This is same-user local evidence, without signatures or protection against someone who can rewrite project code and history. A trusted test command may have side effects or lie, and local write access can tamper with records. Freshness covers the declared local inputs; external services, undeclared ignored inputs and changes restored between observations are outside that guarantee. A pass observes selected test behavior at recorded inputs, not control sufficiency, production assurance, release approval or measured security improvement.
