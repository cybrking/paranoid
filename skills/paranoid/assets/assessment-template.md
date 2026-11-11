# Threat model assessment

## Engineering handoff summary

List the highest-priority scenarios and the controls engineering must build first: priority, threat ID, one-sentence finding, evidence kind, and control IDs. State facts consistent with `model.json`; keep priorities provisional when no organizational policy was supplied. Link `security-controls.md`.

## Scope and system description

Record purpose, in-scope areas, exclusions with reasons, and selected profiles, including why the privacy or AI profile is or is not applied. Describe each in-scope system factually: what it does, where it runs when known, and which out-of-scope systems it depends on. Label described, assumed, and inferred statements; for idea or design inputs, describe intended capabilities rather than invented implementation.

## System model

Render components, trust boundaries, flows, assets, actors, invariants, and assumptions from `model.json` with their IDs and evidence or owner references, so reviewers can read the system the threats depend on without opening the JSON. Generate these tables from the model rather than restating them. Explain any empty boundary or flow inventory.

## Inputs and inventory

Record purpose, assessment date/bundle, input maturity, supplied tickets/features/ideas/designs with locators and revisions/content digests, and any primary/supporting repositories, environment, exclusions, risk policy, and inspected/unavailable/deferred inventory categories. Assign next actions for gaps. Explain any zero boundary/flow inventory.

## Deployment and authorization

Record stated requirements, assumed design, repository intent when available, optional AWS identity/account/region/service scope, collection times, visibility gaps, source → artifact → resource mappings, drift, and effective authorization/tenant enforcement. Mark unknowns explicitly. Do not include credential or customer-data payloads.

## Validation and evidence review

Record `document_valid`, validator identity and output, `coverage_gaps`, `review_gaps`, and independent evidence gaps. State whether validation was executed or blocked. Verify evidence locators and exact claims; schema conformance alone is insufficient.

## Threats and decisions

For each prioritized scenario: ID, harm, impact, feasibility, confidence, evidence/assumptions, response, control, residual risk, owner, and next action. Record accepted-at, authority evidence, review/expiry, and overdue decisions for accepted risks. Keep priorities provisional when no organization policy was supplied.

## Control checks and closure

For each check: ID, scenario/control IDs, passive/active mode, target/environment, authorization reference, executor/time, expected/observed outcome, evidence, and blocked/not-run reasons. For each mitigated scenario record path-specific closure reasoning, reviewer, and unresolved assumptions.

## Engineering handoff

Link `security-controls.md`. Reconcile its IDs, priorities, owners, statuses, and acceptance criteria with the canonical model. Identify requirements before implementation and checks before release.

## Remaining work

List unresolved risks, missing evidence/access, owners or owner-needed markers, and next actions. State `security_effectiveness` and `owner_decision_needed` separately from document validity. Do not assert release readiness without the required policy and authorized decision.
