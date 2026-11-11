# Security fix specs for engineering

Input: AUTH-77 "Sign in with company SSO" (`ticket.md`, sha256:8d2a086f…7f24), bundle `AUTH-77@sha256:8d2a086f19d18faba2619eae02e72b8327bc5aa0a5442b8cdf33916a7fd87f24`
Maturity: idea / design (no code inspected)
Priorities: provisional. No organizational risk policy was supplied.

## Work to prioritize

| Priority | Spec / threats | What to build | Where | Owner | Status |
|---|---|---|---|---|---|
| Critical | SC-01 / T-01, T-05 | Replace email-match auto-linking with owner-proven linking | Account linking step (C-04) | owner needed: ticket owner | proposed; CHK-01 not run |
| High | SC-02 / T-02, T-01 | Verify domain ownership before trusting an IdP for it | SSO setup (C-06) and assertion handling (C-03) | owner needed: ticket owner | proposed; CHK-02 not run |
| High | SC-03 / T-03 | Strict SAML response validation | Assertion consumer service (C-03) | owner needed: eng lead | proposed; CHK-03 not run |
| High | SC-04 / T-04, T-05 | Scope SSO sessions to one workspace | Session issuance (C-08) | owner needed: eng lead | proposed; CHK-04 not run |
| High | SC-05 / T-06 | SSO enforcement and offboarding | Sign-in paths (C-07), sessions (C-08) | owner needed: eng lead | proposed; CHK-05 not run |
| High | SC-07 / T-08, T-09 | Lock down SSO config changes, rotation, recovery | SSO setup (C-06), support runbook | owner needed: ticket owner | proposed; CHK-07 not run |
| Medium | SC-06 / T-07 | Least-privilege JIT role and seat limits | JIT provisioning (C-04) | owner needed: eng lead | proposed; CHK-06 not run |

SC-01 and SC-02 change what the ticket asks for. Settle them before implementation starts. The rest are build requirements and must have passing checks before release.

## Fix specs

### Link existing accounts only with proof from the account owner (SC-01)

- **Risk:** Anyone who controls an IdP can assert a victim's email and, under the ticket as written, be signed straight into the victim's existing account.
- **Fix:** Never link on email match alone. When an SSO email matches an existing account, start a pending link that completes only after the existing account's owner signs in with their current method (or completes a verified-email challenge) and confirms. Store the link as (IdP entity ID, NameID) and match on that pair from then on. Show what the workspace will see before confirming.
- **Where:** Account linking step (C-04), account store (C-05).
- **Done when:**
  - Workspace B's IdP asserting someone else's existing email yields no session, no link, no data.
  - Only the existing owner can complete a pending link.
  - Changing the email at the IdP does not move an existing link to another account.
- **Owner and timing:** owner needed (ticket owner for the requirement change, eng lead for the build). Before implementation.
- **Refs:** T-01, T-05, CTL-01, CHK-01

### Trust an IdP only for domains the workspace proved it owns (SC-02)

- **Risk:** A workspace that claims a domain it does not own (or gmail.com) can provision or impersonate that domain's users.
- **Fix:** Require DNS TXT (or equivalent) domain verification before an IdP is trusted for a domain. Refuse public email domains. One owning workspace per domain. Reject any assertion whose email domain is not verified for the receiving workspace.
- **Where:** SSO setup (C-06), assertion handling (C-03).
- **Done when:**
  - A valid signed assertion for an unverified domain is rejected and creates nothing.
  - Claiming gmail.com is refused at setup.
  - A second workspace cannot claim an already verified domain.
- **Owner and timing:** owner needed (ticket owner). Before implementation.
- **Refs:** T-02, T-01, CTL-02, CHK-02

### Reject any SAML response that is not exactly right (SC-03)

- **Risk:** An outside attacker can forge, wrap, replay or redirect a SAML response and sign in as any SSO user.
- **Fix:** Use a maintained SAML library. Require a signature on the assertion you consume, verified with the workspace's pinned IdP key. Check audience, destination, validity window, InResponseTo, and single use of assertion IDs. Disable DTDs and external entities. Keep IdP-initiated login off by default.
- **Where:** Assertion consumer service (C-03).
- **Done when:**
  - Unsigned, signature-wrapped, wrong-IdP, wrong-audience, expired and replayed responses are each rejected.
  - An unsolicited response does not create a session.
  - A DOCTYPE payload is rejected with no outbound fetch.
- **Owner and timing:** owner needed (eng lead). Before release.
- **Refs:** T-03, CTL-03, CHK-03

### Scope each SSO session to its workspace (SC-04)

- **Risk:** One customer's IdP could give access to the user's other workspaces and personal content.
- **Fix:** An SSO session from workspace X's IdP grants only workspace X. Other workspaces and personal content need their own authentication.
- **Where:** Session issuance and authorization (C-08).
- **Done when:**
  - A user in X and Y who signed in via X gets 403 and no data on Y's resources.
  - Personal content is not returned on an X-only session.
- **Owner and timing:** owner needed (eng lead). Before release.
- **Refs:** T-04, T-05, CTL-04, CHK-04

### Make the IdP authoritative for removal (SC-05)

- **Risk:** An employee removed at the IdP keeps access through an old password or a long-lived session.
- **Fix:** Per-workspace SSO enforcement that blocks other sign-in methods from reaching that workspace. Revoke sessions when enforcement is turned on or a member is removed. Cap SSO session lifetime.
- **Where:** Existing sign-in paths (C-07), sessions (C-08).
- **Done when:**
  - With enforcement on, password login for a removed member returns no workspace data.
  - An old session for a removed member stops working within the configured cap.
- **Owner and timing:** owner needed (eng lead). Before release.
- **Refs:** T-06, CTL-05, CHK-05

### Protect SSO configuration, rotation and recovery (SC-07)

- **Risk:** One phished admin session can swap the IdP and impersonate every member, and a weak support recovery path can bypass SSO.
- **Fix:** Only workspace owners with recent re-authentication may change SSO settings. Log and notify all owners on change. Support two overlapping signing certificates. Write a recovery procedure with strong identity proof, not email alone. Log SSO logins, links and provisioning without raw assertions.
- **Where:** SSO setup (C-06), support runbook.
- **Done when:**
  - A non-owner, or an owner without fresh re-auth, cannot change the IdP certificate; the attempt is logged.
  - A permitted change notifies every owner.
  - Logins keep working through a two-certificate rotation.
- **Owner and timing:** owner needed (ticket owner). Before release.
- **Refs:** T-08, T-09, CTL-07, CHK-07

### Give JIT users the lowest role, within seat limits (SC-06)

- **Risk:** IdP attributes could create admins by default, or provision seats beyond contract.
- **Fix:** New JIT users get the member role. Attribute-to-role mapping is opt-in by an owner. Enforce the workspace seat limit on JIT creation.
- **Where:** JIT provisioning (C-04).
- **Done when:**
  - An assertion with role=admin and no owner mapping creates a member.
  - A JIT login past the seat limit is refused and owners are notified.
- **Owner and timing:** owner needed (eng lead). Before release.
- **Refs:** T-07, CTL-06, CHK-06
