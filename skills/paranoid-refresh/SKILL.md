---
name: paranoid-refresh
description: Update an existing paranoid threat model after the design, ticket or code changes, keeping stable IDs and reopening anything the change made stale.
argument-hint: "[path to existing model.json, default ./threat-model/model.json] [what changed]"
disable-model-invocation: true
license: Apache-2.0
---

Refresh an existing threat model with the `paranoid` skill.

1. Load the `paranoid` skill. Its SKILL.md sits in the sibling folder `../paranoid/` next to this skill's directory; read it and follow its workflow exactly, including its references, validator and honesty rules.
2. Read the existing model (from `$ARGUMENTS`, or `./threat-model/model.json`) and its assessment. Identify what changed since its snapshot: the new ticket text, design or repository revisions.
3. Preserve stable IDs and prior owner decisions. Reopen every assumption, evidence item, check and decision the change affects; do not carry a passed check forward if its target changed.
4. Validate, then rewrite the three artifacts in place only once the new result is ready. Lead your reply with what changed: new or reopened threats and controls, and closed items with the evidence that closed them.
