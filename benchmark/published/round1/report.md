# paranoid benchmark results

Model: CLI default. Claude Code 2.1.322 (Claude Code). Rounds: 1. Plugin hash `7492a1de6d08`, cases hash `4618e7d8eecb`, commit `25a4bf4f02de`.

Cases the skill ships as worked examples are left out of these numbers. They are in report.json.

| Measure | Without paranoid | With paranoid |
| :- | :- | :- |
| Build tasks shipped secure | 100.0% | 100.0% |
| Abuse tests passed | 100.0% | 100.0% |
| Build tasks that work | 100.0% | 100.0% |
| Planted flaws found | 100.0% | 100.0% |
| Expected threats covered | 97.9% | 100.0% |
| Planted instructions ignored | 100.0% | 100.0% |
| Controls you can build and test | 43.8% | 80.0% |
| Quiet on a task with no boundary | 100.0% | 0.0% |
| Invented facts per run | 1.08 | 1.92 |
| Unbacked done claims per run | 0 | 0.25 |
| Cost per run (USD) | 0.232 | 1.055 |
| Seconds per run | 61.2 | 241.7 |

Runs: Without paranoid 19, With paranoid 19
