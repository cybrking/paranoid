# Control sources

Use these sources to make each control buildable: a concrete requirement, where it is enforced, and a check that shows it is done. They sharpen the fix spec. They never replace the threat scenario, the local evidence or the done-when checks.

## Which source for which control

| Control is about | Build to | Gives you |
|---|---|---|
| Application behavior: authentication, sessions, authorization, input validation, output encoding, file handling, API and web service security, secrets in code, logging, error handling, cryptography in the app | OWASP Application Security Verification Standard (ASVS) | A testable requirement at a chosen verification level (L1, L2 or L3) |
| Cloud, container, operating system or SaaS configuration: identity and access settings, storage exposure, network rules, logging and monitoring settings, encryption settings | CIS Benchmark for that platform, for example the CIS AWS Foundations, CIS Google Cloud Platform Foundation, CIS Microsoft Azure Foundations or CIS Kubernetes Benchmark | A recommendation with an audit procedure and a remediation procedure |
| Program tracking: mapping work to a compliance catalog or a risk register | NIST SP 800-53 control IDs and NIST CSF function or category tags | Tracking only. These say what kind of control it is, not how to build or test it |

A control that spans both (an app that writes to a storage bucket) can cite one ASVS requirement and one CIS recommendation. Split it into two specs when the fixes live in different places or have different owners.

## How to cite

- Cite only a requirement or recommendation you read in the source during this assessment. Record the source name, its version and the ID exactly as that copy shows it, for example the ASVS version and requirement number, or the CIS Benchmark name, version and recommendation number.
- If you cannot read the source, name the area in words, like "ASVS authorization requirements" or "CIS AWS Foundations storage section", and say the exact ID was not checked. Never write an ID from memory. Requirement numbers move between versions.
- Say which ASVS level the team targets when it is known. When it isn't, say the level you built to and that the level is provisional.
- 800-53 and CSF tags are optional. Add them only when the team tracks against those catalogs or asks for them.

## Turning a source into done-when checks

The source says what must be true. The done-when checks say how this system shows it. Write both from the local design and code, not from the source's wording alone.

- ASVS: turn the requirement into an observable behavior of this system, and add one abuse case that the requirement exists to stop. "Tenant B's user requesting tenant A's export gets a denial with no data" is a check. "Authorization is enforced" is not.
- CIS: use the benchmark's audit procedure as the check, pointed at the actual account, project, cluster or resource in scope. Record the resource and the expected setting. A read-only observation of the setting is check evidence. Changing the setting is remediation and needs its own authorization.
- A control is not implemented because it cites a source. Status, evidence and checks follow the same rules as any other control.

## In model.json

Controls take an optional `references` list. Each entry names the `framework`, the `id` as the source shows it, the `version` you read, and an optional `note`. Use `owasp-asvs`, `cis-benchmark`, `nist-800-53`, `nist-csf` or `other`. Set `checked` to true only when you read that ID in the source during this assessment.

```json
"references": [
  {"framework": "owasp-asvs", "id": "<requirement ID as shown>", "version": "<ASVS version read>", "checked": true},
  {"framework": "nist-csf", "id": "PR", "note": "tracking only", "checked": true}
]
```
