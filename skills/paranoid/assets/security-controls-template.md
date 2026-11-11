# Security fix specs for engineering

Input: <ticket/feature/idea/design/repositories and snapshot>
Maturity: <idea/design/implementation/deployment>
Priorities: <policy reference or provisional>

## Work to prioritize

| Priority | Spec / threats | What to build | Where | Owner | Status |
|---|---|---|---|---|---|
| <priority> | <spec ID / threat IDs> | <short title> | <logical component or evidenced file/service> | <owner or owner needed> | <proposed/implemented; check pending/verified> |

## Fix specs

One spec per fix. A spec an engineer or agent can run as written, about 90 words. Keep only what is needed to build and verify the fix. Background, residual risk, check procedures, and long dependency notes belong in the assessment and model.json.

### <Short imperative title> (<spec ID>)

- **Risk:** <one sentence: who can do what to what>
- **Fix:** <the change, imperative, one or two sentences. Name the behavior, not a technique, unless the technique is the requirement>
- **Where:** <file, service, or layer. Conditional if undecided>
- **Done when:** <two to four observable checks, including at least one abuse or negative case. No "follow best practices">
- **Owner and timing:** <role or owner needed. before implementation / before release / now / optional hardening>
- **Blocked by:** <only if something truly blocks it. Omit otherwise>
- **Refs:** <threat IDs, control ID, check ID>

Rules:
- One risk per spec. If a control covers two, split it or fix the risk sentence.
- Give a shared requirement one spec and list every threat it closes in Refs.
- Early design specs stay proposed until implementation and checks provide evidence. Never mark a threat mitigated because a spec exists.
- Keep specs no more specific about the exploit than an implementer needs. Detail beyond that stays in the assessment.
- Keep IDs and statuses consistent with model.json.
