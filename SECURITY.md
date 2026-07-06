# Security Policy

## ⚠️ Read this first: the vulnerabilities here are intentional

Prolane is a **deliberately vulnerable** application, built for security training and as a
measurable regression target for a pentest/scanner pipeline. **Finding a vulnerability in the
application is the point - it is not a bug, and we do not want a report for it.**

The intentional vulnerabilities are catalogued in a private ground-truth manifest (the "answer
key"), kept out of this public repo so it does not spoil the exercise. If you found something
exploitable in the app itself, it is almost certainly intentional - please do **not** open a
security report for it.

## What we DO want reported

Defects in the scaffolding around the intentional bugs - the parts meant to be correct:

- The **launcher or setup** is broken (`run.py`, `docker compose up`, dependency install, seeding).
- The app **crashes or errors in a way that is clearly not one of the intended vulnerabilities**.
- A **real, non-intentional security flaw in the non-vulnerable chassis**.
- **Documentation that is wrong or misleading** (README / quickstart / this file).

### How to report

Open a GitHub issue: what you expected vs. observed, and steps to reproduce.

## Safety boundaries (non-negotiable)

- **Never deploy this on the public internet** or any untrusted network. localhost / a private
  dev network only; defaults bind to localhost, never `0.0.0.0`.
- **All secrets in this repo are fake** and clearly labelled. Do **not** submit a PR that adds a
  real credential, key, token, or any real PII - it will be rejected.
- Out-of-band / SSRF exercises must hit a **local sink**, never a real external callback.

## Supported versions

Pre-v1 training software with no security-support guarantees. Use only as described above.
