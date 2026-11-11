# Benchmark

The same agent, the same model and the same inputs, once with paranoid and once without.
Nothing here has run yet. Numbers go in the main README only after a real run.

## What it measures

| Set | Cases | How it's scored |
| :- | :- | :- |
| Build tasks | 7 small apps with one function to write, like an export download, an avatar from a URL or a payment webhook. Six cross a trust boundary. One doesn't. | Hidden tests, no judgment involved. Functional tests check the feature works. Abuse tests check the access check, the SSRF guard, the signature check and so on. The quiet task checks he stays silent when there's no boundary |
| Tickets | 10 feature tickets and ideas with no code. Four carry a planted instruction to skip findings | A blind judge checks each output against a key of expected threats written before any run |
| Repositories | 4 small repos with 19 planted flaws. Three carry a planted instruction aimed at reviewers | The same blind judge, against the planted flaws and where they live |

Every build task ships a secure and an insecure reference solution. `check_keys.py` proves the
secure one passes every hidden test and the insecure one passes the functional tests but fails
at least one abuse test, so a pass means the code really is safer.

In the build tasks both conditions get the identical prompt. The only difference is whether the
plugin is loaded, so the result measures always on mode. For tickets and repositories the
paranoid condition uses `/paranoid:paranoid-ticket` or `/paranoid:paranoid-repo` and the other
condition gets a plain request for a threat model.

The judge sees each output with the tool's name removed, in shuffled order, and every "covered"
verdict must quote the output word for word or it doesn't count. `score.py sheet` writes a blind
spreadsheet so a person can check the judge.

## Run it

You need Claude Code signed in and Python 3.10 or later. Every run is a real Claude Code session,
so it uses your Claude usage. Start small.

```sh
git clone https://github.com/cybrking/paranoid.git && cd paranoid
python3 benchmark/check_keys.py                       # prove the cases are fair, no model calls
python3 benchmark/run.py --dry-run                    # see the plan and the exact command
python3 benchmark/run.py --cases B01 T03 R01          # a 6 run pilot
python3 benchmark/run.py --rounds 1 --out benchmark/results/pilot   # all 21 cases, 42 runs
python3 benchmark/score.py all benchmark/results/pilot
```

`score.py all` runs the hidden tests, asks the judge once per ticket and repository run, and writes
`report.md`, `report.json` and `chart.svg` into the results folder. The full plan is five rounds
(`--rounds 5`, 210 runs). Rerun the same command with the same `--out` to resume.

Each run happens in a fresh copy of the case folder, with `acceptEdits` permissions, Python test
commands allowed, and web access blocked. Your user settings and installed plugins are not loaded
(`--setting-sources project,local`). Your personal CLAUDE.md still is, in both conditions. Pass
`--bare` with an API key to leave it out too.

## Honest limits

- Two tickets come from the skill's own worked examples. They are scored but left out of the headline.
- The judge is a model. The quote rule and the blind sheet are there so you can check it.
- Small apps are not your codebase. The build tasks show whether the habit is there, not every case it covers.
