# Project Management DVWA

A modern, deliberately vulnerable, API-first web application for hands-on web and API security training - and a measurable regression target for pentest and scanner pipelines.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Status: in development](https://img.shields.io/badge/status-in%20development-orange.svg)](#)

> **WARNING: This application is intentionally vulnerable.** It is for local, educational use only. Do NOT deploy it on the public internet, a shared network, or anywhere reachable by untrusted users. Every secret in this repo is fake.

## What is this?

Project Management DVWA is a **deliberately vulnerable web application** and **vulnerable API** - a realistic project-and-task management SaaS planted with intentional security bugs, built as a **modern DVWA alternative**. The classic teaching apps (DVWA, bWAPP, OWASP WebGoat, Mutillidae) are ~2013-era PHP/Java form apps. This project instead targets the **OWASP API Security Top 10 (2023)** alongside the OWASP Web Top 10 (2021) and current attack techniques, giving you a realistic **API penetration testing lab** and a **web security training** ground that reflects how software is actually built today - covering **IDOR, BOLA, SSRF, JWT** flaws and much more.

It ships as **two distinct origins on purpose**: a `web` origin (Next.js 14, App Router, TypeScript) on `http://localhost:8082` that issues an httpOnly session cookie, and an `api` origin (FastAPI, Python) on `http://localhost:8081` that authenticates with a Bearer JWT. The browser logs into `web`, then exchanges its session cookie for an `api` Bearer token - a cookie-to-Bearer bridge across two hosts, exactly the kind of surface a real IDOR, BOLA, SSRF, or JWT bug lives on.

Every one of the 40+ catalogued vulnerabilities is paired with a secured "twin" and a self-test that proves it fires. A machine-readable ground-truth manifest is the answer key, so it doubles as a measurable regression target for scanners and pentest automation.

## Vulnerability coverage

- **Access control:** BOLA/IDOR, broken function-level authorization (BFLA), mass assignment / BOPLA, excessive data exposure
- **SSRF:** classic SSRF, SSRF to cloud metadata, and second-order SSRF via OAuth dynamic client registration
- **Injection:** SQL injection (behind a signature WAF), server-side template injection (SSTI) to RCE, OS command injection, insecure deserialization, path traversal
- **Auth & tokens:** JWT attacks (weak HMAC secret, `alg:none`, embedded JWK header), OAuth2/OIDC flaws (PKCE downgrade, loose `redirect_uri`), SCIM provisioning abuse, no-rate-limit brute force
- **Integrations & logic:** webhook SSRF / replay / signature bypass, race conditions (TOCTOU), business-logic abuse (refund/coupon/seat limits)
- **Client & web:** stored and DOM-based XSS, prototype pollution, secrets in the JS bundle, CORS misconfiguration, clickjacking, open redirect
- **Realtime:** WebSocket BOLA/BFLA

Plus scanner-baiting decoy endpoints and a two-face (lab vs challenge) build.

## Tech stack

Python 3.11+, FastAPI, Next.js 14 (App Router, TypeScript), SQLite (deterministically seeded). Web on `http://localhost:8082`, API on `http://localhost:8081`.

## Quickstart

```sh
pip install -r api/requirements.txt
cd web && npm install && cd ..

make dev-api      # or: python -m uvicorn api.main:app --port 8081 --reload   -> api on http://localhost:8081
make dev-web      # or: cd web && npm run dev                                 -> web on http://localhost:8082
```

## Seeded accounts

Two tenants plus a super-admin enable cross-tenant and broken-access-control bugs. All passwords are `Password1!`.

| Email | Tenant | Role |
| --- | --- | --- |
| alice@acme.test | Acme | Owner |
| charlie@acme.test | Acme | Member |
| bob@globex.test | Globex | Owner |
| diana@globex.test | Globex | Member |
| superadmin@vulnforge.internal | - | Super-admin |

## Reporting

The vulnerabilities in this project are **intentional** - please do not report them as security issues. If you find a real bug in the test harness or the ground-truth manifest, see [SECURITY.md](SECURITY.md).

## License

MIT - see [LICENSE](LICENSE).
