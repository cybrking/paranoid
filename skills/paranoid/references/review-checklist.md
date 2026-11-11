# Required substantive review

The draft schema checks recorded relationships, not whether the agent inspected all relevant sources. This checklist compensates for known contract gaps while the skill is piloted. Record results in `assessment.md`; do not mistake passing the helper for completing these checks.

| Review | Required reasoning / record |
|---|---|
| Inventory | For application, authorization/tenancy, workers, data, infrastructure, dependencies, CI/CD, deployment, and external integrations: inspected, not applicable with rationale, unavailable, or deferred. Every actionable gap has an owner or owner-needed marker and a next action. Explain zero boundaries/flows. |
| Component coverage | Review relevant internal components and privilege/tenant transitions even when no declared network boundary crosses them. Confirm entry points and public/admin paths against source. |
| Provenance | Give each evidence locator its actual input revision/content digest (ticket/design/idea/repo) or AWS resource observation time. `snapshot` refers to the assessment bundle under draft 0.2. State bundle membership in the report; a matching string alone does not establish freshness. |
| Deployment | Connect repo revision to built artifact/digest and deployed resource when possible. Mark the mapping verified, claimed, mismatch, or unknown; configuration existing in a repo does not establish deployed state. |
| Effective authority | Identify principal, action, resource, context, tenant identity source, and enforcement point. Inspect relevant policy layers or record gaps. A single policy or network diagram does not establish effective access. |
| Check execution | State passive/active mode, actual target/environment, authorization reference for active checks, executor, time, expected and observed outcome, and evidence. No execution authorization can be inferred from a threat model. |
| Closure | For each mitigated scenario, explain which attack steps the closure controls address and why the linked checks support that claim. Passing a logging check alone cannot establish that disclosure is prevented. Record the reviewer and unresolved assumptions. |
| Lifecycle | `response: accept` and `status: accepted` must agree and have authorized acceptance; track accepted-at, review/expiry date, authority evidence, and overdue decisions in the report. Record stale assumptions and explicit dismissal rationale. |
| Risk policy | Link organizational policy when available; otherwise priorities are provisional and acceptance/release readiness remains undecided. Unknown feasibility is not low feasibility. |
| Cloud visibility | Enumerate intended and observed account/region/service scope, collection time, denied calls, incomplete pagination, and omitted policy layers. Read-only credentials can still expose sensitive payloads; inspect scoped configuration/metadata only. |
| Independent review | Re-read evidence against the precise claims and challenge prerequisites and closure relevance in a separate pass. Another model may share the same blind spots; record its findings and reconcile them rather than counting agreement as proof. |


For non-code inputs, review maturity and provenance, ensure described versus assumed architecture is explicit, and keep inferred weaknesses as hypotheses. Engineering controls must have matching canonical IDs, owners or owner-needed markers, concrete requirements, and testable acceptance criteria; proposed requirements do not establish implemented mitigation.
