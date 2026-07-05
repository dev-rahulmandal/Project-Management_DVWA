# Security Policy

## ⚠️ Read this first: the vulnerabilities here are intentional

VulnForge is a **deliberately vulnerable** application, built for security training and as a
measurable regression target for a pentest/scanner pipeline. **Finding a vulnerability in the
application is the point - it is not a bug, and we do not want a report for it.**

Every intentional vulnerability is already catalogued in
[`ground-truth/manifest.yaml`](ground-truth/manifest.yaml) (the "answer key") with a test that
proves it fires. If you found something exploitable in the app, it is almost certainly already in
that manifest. Please do **not** open a security report for it.

## What we DO want reported

Report defects in the **harness, manifest, or test infrastructure** - the parts that are supposed
to be correct:

- A **manifest entry whose vuln does not actually fire** (or fires differently than described).
- A **planted vulnerability that is missing from the manifest** (a vuln with no answer-key entry).
- A **secured twin (negative control) that is actually exploitable** (the "safe" version isn't).
- A **bug in the self-test** (`tools/verify.py` / `tests/`) - false pass, false fail, flakiness, or
  a control/exploit test that doesn't test what it claims.
- **Manifest/schema inconsistencies**, broken repro steps, or incorrect CWE/OWASP/detector fields.
- Anything that makes VulnForge an **unreliable answer key** for the pipeline that regresses
  against it.

### How to report a harness/manifest bug

Open a GitHub issue describing: the manifest id (if relevant), what you expected vs. what you
observed, and steps to reproduce (ideally a failing `make verify` excerpt).

## Safety boundaries (non-negotiable)

- **Never deploy this on the public internet** or any untrusted network. It is intended for
  `localhost` / a private dev network only; defaults bind to localhost, never `0.0.0.0`.
- **All secrets in this repo are fake** and clearly labelled as such. Do **not** submit a PR that
  adds a real credential, key, token, or any real PII - that will be rejected.
- Out-of-band / SSRF exercises must hit a **local sink**, never a real external callback.

## Supported versions

This is pre-v1 training software with no security-support guarantees. Use only as described above.
