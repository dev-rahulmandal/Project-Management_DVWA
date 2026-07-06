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

Every catalogued vulnerability is paired with a secured "twin" as a negative control. The catalog is maintained against a machine-readable ground-truth manifest - an answer key that also serves as a regression fixture for scanners and pentest automation - which is kept out of the public repo so it does not spoil the exercise.

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

Requires **Python 3.11+** and **Node.js 18.17+**. One cross-platform command installs everything and runs both servers (on macOS/Linux use `python3` if `python` is missing):

```sh
git clone https://github.com/dev-rahulmandal/Project-Management_DVWA.git
cd Project-Management_DVWA
python run.py
```

On first run `run.py` installs the Python and web dependencies and seeds the local `.env` files, then starts:

- **api** (FastAPI) on http://localhost:8081
- **web** (Next.js) on http://localhost:8082

Open http://localhost:8082 and sign in with a seeded account below. Press Ctrl-C to stop both servers. `python run.py` runs the realistic default face; add `python run.py --lab` for the development/lab mode (the in-app secured comparisons and the API docs).

### Run with Docker

Prefer containers? With [Docker](https://docs.docker.com/get-docker/) and the Compose v2 plugin, one command builds and runs the whole system - no Python or Node needed on the host:

```sh
git clone https://github.com/dev-rahulmandal/Project-Management_DVWA.git
cd Project-Management_DVWA
docker compose up --build
```

Open http://localhost:8082, then press Ctrl-C to stop and run `docker compose down` to remove the containers. The SQLite database is seeded fresh inside the container on every run - it is intentionally ephemeral, so each `up` starts from a clean, deterministic answer key. Ports publish to `127.0.0.1` only.

> On Debian/Kali the `docker.io` engine ships without Compose. If `docker compose` reports an unknown command, install the plugin per [Docker's install docs](https://docs.docker.com/compose/install/linux/) - the manual binary drop-in into `/usr/local/lib/docker/cli-plugins/` is the most reliable method.

<details>
<summary>Manual setup (without the launcher)</summary>

```sh
pip install -r api/requirements.txt
cd web && npm install && cd ..
cp api/.env.example api/.env
cp web/.env.example web/.env.local

python -m uvicorn api.main:app --port 8081 --reload   # api -> http://localhost:8081
cd web && npm run dev                                  # web -> http://localhost:8082
```
</details>

> **Optional (realistic pentest setup):** to let a proxy like Burp observe api traffic (browsers bypass the proxy for localhost), set `NEXT_PUBLIC_API_ORIGIN=http://api.prolane.test:8081` in `web/.env.local` and add `127.0.0.1  prolane.test api.prolane.test` to your hosts file.

## Seeded accounts

Two tenants plus a super-admin enable cross-tenant and broken-access-control bugs. All passwords are `Password1!`.

| Email | Tenant | Role |
| --- | --- | --- |
| alice@northwind.test | Northwind Systems | Owner |
| charlie@northwind.test | Northwind Systems | Member |
| bob@bluepeak.test | Bluepeak Labs | Owner |
| diana@bluepeak.test | Bluepeak Labs | Member |
| marcus.webb@northwind.test | Northwind Systems | Owner + Super-admin |

## Reporting

The vulnerabilities in this project are **intentional** - please do not report them as security issues. If you find a genuine bug in the app scaffolding, the launcher, or the docs (not one of the intended vulnerabilities), see [SECURITY.md](SECURITY.md).

## License

MIT - see [LICENSE](LICENSE).
