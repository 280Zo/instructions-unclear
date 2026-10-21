---
root: true
targets: ["*"]
description: "Secure coding: the security mistakes AI-written code makes most often, and how to avoid them"
---

# Secure Coding

Applies to any code, configuration, script, pipeline or container you write or change.

* Treat all external input (users, files, network, environment, other services) as untrusted. Validate type, format and length where it enters.
* Never build SQL, shell commands, HTML or file paths by joining strings with untrusted data. Use parameterized queries, argument lists instead of a shell (no `shell=True`, no `eval`/`exec` on input), context-aware output encoding, and normalized paths checked against an allowed root.
* Never put secrets, tokens or keys in code, config, logs, tests or examples. Read them from environment variables or a secret store.
* Check authentication and authorization on the server for every protected action. Deny by default.
* Use established libraries for cryptography, password hashing (Argon2, bcrypt or scrypt) and sessions. Never write your own, never use MD5 or SHA-1 for security, and compare secrets in constant time.
* Fail closed: an error must never grant access or skip a check. Show users generic error messages; keep stack traces and internal details in server-side logs, and never log secrets or personal data.
* Default to secure settings: TLS for production and deployed configuration, strong algorithms, least privilege for processes, files, tokens and cloud roles. Never disable certificate verification, allow any origin with credentials, or ship debug mode. Local development without TLS is not a finding. Recommend HSTS only as a deliberate deployment decision, and explain its lock-in risk.
* Before adding a dependency, confirm it exists, is maintained and is the exact package you meant. AI assistants often suggest packages that don't exist or have look-alike names.
* In containers and CI: run as non-root, pin images by digest and actions by commit SHA, and take secrets from the platform's secret store.
* Add negative tests for security-critical code: rejected input, unauthorized access, failure paths.
* Before finishing, review your change against this list and fix what you find. If a security scanner is available (Semgrep, CodeQL, Bandit, `npm audit`, `pip-audit`), run it on the changed code. Never report a scan you did not run.
* If a change needs a security decision you can't make (threat model, compliance, choice of cryptography), say so instead of guessing.
