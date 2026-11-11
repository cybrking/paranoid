# Threat Model: AUTH-77, Sign in with company SSO (SAML)

## 1. What is being built

- Each enterprise customer (tenant) configures their own SAML identity provider (IdP) for their workspace.
- Users sign in through that IdP. Our app is the Service Provider (SP) and consumes SAML assertions at an Assertion Consumer Service (ACS) endpoint.
- **Auto-linking:** if the email in the assertion matches an existing account, the SSO login is linked to that account.
- **Just-in-time (JIT) provisioning:** a first-time user "from the customer's domain" gets an account and is added to that customer's workspace.

## 2. Assets

| Asset | Why it matters |
|---|---|
| User accounts and their data | The main target. Auto-linking hands an existing account's data to whoever passes SSO. |
| Workspace membership and roles | JIT decides who joins a workspace. Getting this wrong gives outsiders access to tenant data. |
| Tenant SSO configuration (IdP metadata, signing certs, domains) | Whoever controls this controls who can log in as anyone in the tenant. |
| Session tokens issued after SSO | Same value as a password login. |
| SP signing/decryption keys | Used to sign AuthnRequests and decrypt assertions. |

## 3. Trust boundaries and actors

- **Browser to ACS endpoint.** The SAML response arrives through the user's browser, so the browser can change it. Treat every byte as attacker-controlled until the signature is validated.
- **Tenant IdP to our app.** We trust an IdP only for identities **it is authoritative for**. A tenant's IdP is fully controlled by that tenant's admin, and **anyone can sign up as a tenant and point it at an IdP they run**. This is the most important boundary in the feature.
- **Tenant admin to SSO config.** Tenant admins are trusted inside their own tenant. They are not trusted for other tenants or for email domains they have not proven they own.

Threat actors:
1. A malicious or compromised tenant: an attacker who signs up, enables SSO, and runs their own IdP (Okta dev account, Keycloak, a self-hosted SimpleSAMLphp).
2. An external attacker who forges, tampers with or replays SAML responses.
3. A former employee whose IdP account was disabled but who still has an app session or a password.
4. A legitimate user at a customer with weak IdP hygiene (for example, users can edit their own email attribute in the IdP).

## 4. Threats (STRIDE), ranked

### T1. CRITICAL: Account takeover through email-based auto-linking
**Spoofing / Elevation.** The ticket says "an account with the same email already exists, link them automatically." The email in a SAML assertion is just a string the IdP chooses to put there. An attacker creates a tenant, configures their own IdP, and issues an assertion with `email=ceo@victim-corp.com`. The app finds the existing account and links it. The attacker now owns the victim's account and data, with no password and no MFA.
Variants:
- The victim is a personal or password user at a company that never set up SSO.
- The victim belongs to a *different* tenant that does use SSO.
- A legitimate customer IdP lets users set their own `mail` attribute (common in Azure AD/Entra and in custom attributes), so a normal employee can take over a colleague's or an admin's account.
- Email normalization tricks: case, Unicode lookalikes, `+tags`, trailing dots, and `user@victim.com` vs `user@VICTIM.com.` in lookups.

### T2. CRITICAL: Cross-tenant JIT provisioning through unverified domains
**Elevation / Information disclosure.** "New users from the customer's domain" means some tenant has to be mapped to some domain. If a tenant admin can claim any domain (for example `gmail.com` or a competitor's domain) without proving ownership, then:
- That tenant's IdP can mint users at that domain, and T1 gets worse.
- If domain routing happens at login (user types email, we pick the IdP by domain), a squatter can intercept other people's logins.
- A real customer's employees might be JIT-added to the attacker's workspace, or the reverse.

### T3. CRITICAL: SAML response forgery and signature bypass
**Spoofing / Tampering.** These are the standard SAML implementation bugs, and each one leads to full authentication bypass:
- Unsigned assertions accepted, or only the Response signed while the Assertion is not (or the reverse) and the code reads the unsigned part.
- XML Signature Wrapping (XSW): the signature validates over one element while the app reads identity from another one that was injected.
- XML comment and canonicalization truncation (`user@evil.com<!---->.victim.com`), as in the 2018 CVE class affecting several libraries.
- Accepting the certificate embedded in `KeyInfo` in place of the pinned tenant cert.
- Weak algorithms (RSA-SHA1, no digest check).
- Validating the signature against **any** tenant's cert in place of the tenant the response is for. This lets tenant A's IdP sign assertions for tenant B.

### T4. HIGH: Replay and assertion injection
**Spoofing.** A captured SAMLResponse (from logs, proxies, browser history, a leaked HAR file) is replayed. A response meant for another SP (same IdP, different app) is sent to our ACS. Unsolicited IdP-initiated responses make login CSRF and injection easier.

### T5. HIGH: XML parser attacks on the ACS endpoint
**Information disclosure / DoS.** XXE (reading local files, SSRF to cloud metadata), billion-laughs entity expansion, very large or deeply nested documents. Also an XSLT transform in the signature that runs code. The ACS is unauthenticated, so this is attack surface open to anyone on the internet.

### T6. HIGH: Malicious or careless SSO configuration changes
**Tampering / Elevation.** Someone who gets into a tenant admin session (or a low-privilege member, if authorization is missing) swaps the IdP metadata or signing cert to their own IdP. After that they can log in as anyone in the tenant. Fetching metadata from a URL the admin supplies is also an SSRF vector.

### T7. HIGH: SSO bypass and stale access after offboarding
**Elevation.** The customer's reason for SSO is central control, but:
- Users can still log in with an old password or a social login, getting around IdP MFA and offboarding.
- Sessions live past IdP deprovisioning. JIT creates users and does not remove them.
- Password reset by email lets someone who still controls the mailbox (or a reused address) back in.

### T8. MEDIUM: Over-privileged JIT users
**Elevation.** JIT users get a default role higher than intended, or role and group attributes from the assertion are trusted without a mapping the tenant controls. A user then gives themselves admin through an IdP attribute they can edit.

### T9. MEDIUM: Open redirect and session handling at the ACS
**Spoofing / Information disclosure.** `RelayState` used as the redirect target with no check lets an attacker send users to a phishing page after a real login. The session ID is not rotated at login (session fixation). Login CSRF lets an attacker sign a victim into the attacker's account.

### T10. MEDIUM: Account enumeration and tenant discovery
**Information disclosure.** Home-realm discovery ("enter your email") shows which companies are customers and which emails exist, through different responses or timing.

### T11. MEDIUM: Missing audit trail
**Repudiation.** Without logs of link events, provisioning, config changes and failed validations, a takeover through T1 or T6 cannot be found or investigated.

### T12. LOW: SAML data leaking into logs
**Information disclosure.** Full SAMLResponse blobs logged at debug level can be replayed (T4) and contain PII.

## 5. Security controls engineering should build

### A. Identity linking (fixes T1). Required before launch
1. **Do not link by email on its own.** Key SSO identities on `(tenant_id, IdP entityID, NameID or a stable subject attribute such as an immutable object ID)`. Email is a display attribute, not an identifier.
2. **Only link automatically when the email's domain is verified by that same tenant** (see B), and the existing account already belongs to that tenant, or is unaffiliated with a matching verified domain.
3. **For any other match, require proof of the existing account before linking.** The user signs in to the existing account (password plus MFA) or clicks a one-time link sent to that email, then confirms the link. Never link an account that belongs to another tenant.
4. Never auto-link an account that has admin or owner rights anywhere without that step-up proof.
5. Normalize emails one way everywhere (Unicode NFKC, lowercase, strip trailing dot). Reject confusable or mixed-script domains. Do not treat `+tags` as the same address unless policy says so.
6. Tell the account owner by email whenever a new SSO identity is linked, with a one-click "this wasn't me" that unlinks it and locks the account.
7. Once linked, look up later logins by the stored subject, not email. If the email in the IdP changes, update it only inside verified domains.

### B. Domain ownership (fixes T2)
1. A tenant must **verify each domain** (DNS TXT record) before it is used for JIT, auto-linking or login routing.
2. One verified domain belongs to one tenant at a time. Disputes go through support by hand.
3. Block public and free-mail domains (gmail.com, outlook.com and similar) and the public suffix list.
4. Check DNS again on a schedule. If the record goes away, suspend JIT and linking for that domain.
5. JIT creates a user only when the asserted email is in a domain verified by **the tenant whose IdP signed the assertion**.

### C. SAML validation (fixes T3, T4, T5)
1. Use a maintained, well-reviewed SAML library (for example python3-saml/OneLogin, ruby-saml at current version, Shibboleth, or the identity platform's built-in SAML). Do not hand-roll XML signature checks. Track library CVEs.
2. Find the tenant **before** validation, from our own ACS URL (`/sso/saml/{tenant_id}/acs`) or the stored request state. Validate only against **that tenant's pinned signing cert(s)**. Ignore `KeyInfo` certs.
3. Require a valid signature on the Assertion (and on the Response if the library supports it). Read identity **only** from the exact element whose signature was checked. Reject responses with more than one Assertion.
4. Allow only RSA-SHA256 or stronger. Reject SHA-1, no transforms other than the standard enveloped and exclusive-c14n ones.
5. Check `Issuer` equals the tenant's configured IdP entityID, `Audience` equals our SP entityID, `Recipient` and `Destination` equal this ACS URL, `NotBefore` and `NotOnOrAfter` (allow at most 2 to 3 minutes of clock skew), `SubjectConfirmationData` and `StatusCode = Success`.
6. **SP-initiated flow by default.** Store the AuthnRequest ID in the user's session and require `InResponseTo` to match it, then delete it so it can only be used once.
7. **Replay cache:** store assertion IDs until they expire and reject repeats.
8. IdP-initiated login is off by default. If a tenant turns it on, apply the replay cache and a short validity window, and show a confirmation page before the session starts.
9. Hardened XML parsing: no DTDs, no external entities, no XInclude, no XSLT transforms. Limit body size (for example 256 KB) and nesting depth. Rate limit the ACS per IP and per tenant.
10. Optionally require encrypted assertions (SP decryption key in a KMS or secrets manager, rotated).

### D. SSO configuration security (fixes T6)
1. Only tenant owners or admins can change SSO settings. Check this on the server.
2. Require recent re-authentication (step-up MFA) to change IdP metadata, certs or domains.
3. Email all tenant admins when SSO config changes, and keep the old config so it can be rolled back.
4. Let admins test a new config before it goes live, so a broken config does not lock everyone out. Keep a break-glass admin login that is MFA-protected and logged.
5. If metadata is fetched by URL: HTTPS only, block internal and link-local IPs (including 169.254.169.254) and redirects to them, set timeouts and a size limit. Better: accept uploaded metadata XML or a pasted cert.
6. Track cert expiry and warn admins ahead of time. Support two certs during rotation.

### E. Enforcement and lifecycle (fixes T7, T8)
1. Per-tenant **"Require SSO"** setting. When it is on, password login, social login and password reset are turned off for users in that tenant's verified domains (except the break-glass admin).
2. Short app session lifetime for SSO users (for example 8 to 12 hours) and re-authentication through the IdP after that. Support SAML Single Logout where possible.
3. Support **SCIM** deprovisioning (or at least an admin "remove user" that kills all sessions and API tokens right away). JIT alone cannot remove access.
4. JIT users get the **lowest** role by default. Role and group mapping from assertion attributes only through an allowlist the tenant admin sets up. Never give admin through a JIT attribute without explicit config.
5. Tenant admins can turn JIT off and require approval for new users.
6. Revoke all sessions and tokens when a user is unlinked, removed or the SSO config changes.

### F. Session and redirect handling (fixes T9, T10)
1. Rotate the session ID after a successful ACS login. Set session cookies `Secure`, `HttpOnly`, `SameSite=Lax`.
2. `RelayState`: store an opaque value server-side, or allow only relative paths on our own origin. Never redirect to an absolute URL taken from it.
3. Bind the login to the browser that started it (state stored in the session) to stop login CSRF.
4. Home-realm discovery returns the same response and similar timing whether or not the email or domain is known. Rate limit it.

### G. Logging, monitoring and response (fixes T11, T12)
1. Audit log entries for: SSO login success and failure (with reason), new identity link, JIT account creation, role changes, SSO config and domain changes, Require-SSO changes. Include tenant, IdP entityID, subject, IP and user agent.
2. Alert on: links to accounts outside the tenant (should never happen after A), many signature or replay failures, a sudden spike in JIT creations, and config changes followed by logins straight away.
3. Never log full SAMLResponse bodies or certs' private parts. Redact assertions in error logs.
4. Show admins an audit view of SSO events in their tenant.

## 6. Tests engineering should add

- Assertion signed by tenant A's IdP for an email in tenant B's verified domain is rejected and nothing gets linked.
- Assertion with an email matching an existing password account outside a verified domain does **not** link and starts the proof flow in A3.
- XSW variants (the 8 standard ones from SAML Raider), comment injection in NameID, unsigned assertion, assertion signed with a `KeyInfo` cert, SHA-1 signature: all rejected.
- Replayed assertion, expired assertion, wrong Audience, wrong Destination, mismatched `InResponseTo`: all rejected.
- XXE and billion-laughs payloads to the ACS: rejected with no outbound request and no memory spike.
- `RelayState=https://evil.example` does not redirect off-site.
- With Require SSO on, password login and password reset fail for domain users.
- SCIM or admin removal kills existing sessions within seconds.
- Non-admin member cannot read or change SSO config. Admin change without step-up fails.

## 7. Suggested ticket changes

The ticket as written ("same email already exists, link them automatically") is an account takeover bug by design. Change the acceptance criteria to:

> Link automatically only when the email's domain is verified by the tenant whose IdP signed the assertion and the account is not owned by another tenant. Otherwise, the user must prove they own the existing account before linking. New users are created by JIT only in verified domains, with the lowest role.

Split out two follow-up tickets that the feature needs to be safe for enterprise customers: **domain verification** (B) and **Require SSO plus SCIM deprovisioning** (E1 to E3). Domain verification has to ship before or together with AUTH-77.
