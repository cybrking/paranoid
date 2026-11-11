---
name: paranoid-repo
description: Threat model an existing codebase: map entry points, trust boundaries, data stores and deployment paths, then rank the threats and the controls to build first.
argument-hint: "[repository paths; defaults to the current repository]"
disable-model-invocation: true
license: Apache-2.0
---

Run the `paranoid` skill on one or more repositories.

1. Load the `paranoid` skill. Its SKILL.md sits in the sibling folder `../paranoid/` next to this skill's directory; read it and follow its workflow exactly, including its references, validator and honesty rules.
2. Scope: the repositories in `$ARGUMENTS`, or the current repository when none are named and it is unambiguous. Pin the inspected revisions and note uncommitted changes.
3. Read-only by default: inspect source, do not run the repository's scripts, install its dependencies, test actively or touch cloud resources unless the user separately authorizes it. Keep code, intended infrastructure and observed deployment as separate evidence.
4. Write the three artifacts to `./threat-model/` unless the user names another path. Lead your reply with the ranked controls and what to fix first, then the visibility gaps.
