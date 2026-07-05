-- VulnForge database schema - SQLite (dev).
-- When Docker integration is added at v1, a Postgres version replaces this.
-- Application code is DB-agnostic; only this file and seed.sql change.
--
-- Note: SQLite foreign keys are OFF by default.
-- The app must run `PRAGMA foreign_keys = ON` at every connection.

CREATE TABLE organizations (
  id             INTEGER PRIMARY KEY,
  name           TEXT NOT NULL,
  slug           TEXT NOT NULL UNIQUE,
  plan_tier      TEXT NOT NULL DEFAULT 'starter',  -- 'starter' | 'pro' | 'enterprise'
  credit_balance INTEGER NOT NULL DEFAULT 0        -- billing credits
);

CREATE TABLE users (
  id              INTEGER PRIMARY KEY,
  org_id          INTEGER NOT NULL REFERENCES organizations(id),
  email           TEXT NOT NULL UNIQUE,
  full_name       TEXT NOT NULL,
  role            TEXT NOT NULL DEFAULT 'member',  -- 'member' | 'admin' | 'owner'
  is_super_admin  INTEGER NOT NULL DEFAULT 0,       -- 0=false 1=true
  is_active       INTEGER NOT NULL DEFAULT 1,       -- 0=deactivated (cannot sign in)
  password_hash   TEXT NOT NULL,
  internal_notes  TEXT,                             -- intentional BOPLA over-exposure target
  external_id     TEXT,                             -- SCIM externalId (opaque IdP label)
  created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE projects (
  id             INTEGER PRIMARY KEY,
  org_id         INTEGER NOT NULL REFERENCES organizations(id),
  name           TEXT NOT NULL,
  description    TEXT,
  status         TEXT NOT NULL DEFAULT 'active',    -- 'active' | 'archived'
  created_by_id  INTEGER NOT NULL REFERENCES users(id),
  deleted_at     TEXT,                              -- soft-delete (archive/restore surface)
  created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
  id           INTEGER PRIMARY KEY,
  project_id   INTEGER NOT NULL REFERENCES projects(id),
  org_id       INTEGER NOT NULL REFERENCES organizations(id),
  title        TEXT NOT NULL,
  body         TEXT,                                -- intentional stored-XSS target
  assignee_id  INTEGER REFERENCES users(id),
  status       TEXT NOT NULL DEFAULT 'open',        -- 'open' | 'in_progress' | 'done'
  priority     TEXT NOT NULL DEFAULT 'medium',      -- 'low' | 'medium' | 'high'
  due_date     TEXT,                                -- ISO date, nullable
  deleted_at   TEXT,                                -- soft-delete (archive/restore surface)
  created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Threaded task comments.
CREATE TABLE comments (
  id         INTEGER PRIMARY KEY,
  task_id    INTEGER NOT NULL REFERENCES tasks(id),
  org_id     INTEGER NOT NULL REFERENCES organizations(id),
  author_id  INTEGER NOT NULL REFERENCES users(id),
  body       TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE invitations (
  id          INTEGER PRIMARY KEY,
  org_id      INTEGER NOT NULL REFERENCES organizations(id),
  email       TEXT NOT NULL,
  role        TEXT NOT NULL DEFAULT 'member',
  token       TEXT NOT NULL UNIQUE,
  expires_at  TEXT NOT NULL,
  created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_logs (
  id             INTEGER PRIMARY KEY,
  org_id         INTEGER,
  user_id        INTEGER,
  action         TEXT NOT NULL,
  resource_type  TEXT,
  resource_id    INTEGER,
  ip             TEXT,
  created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Promo coupons: single-use redeem (TOCTOU race surface: API-RACE-001) and a
-- percentage discount used by billing checkout.
CREATE TABLE coupons (
  id              INTEGER PRIMARY KEY,
  code            TEXT NOT NULL UNIQUE,
  remaining_uses  INTEGER NOT NULL,
  discount_pct    INTEGER NOT NULL DEFAULT 0
);

-- Personal access tokens (scoped API keys). Only the SHA-256 hash is stored.
CREATE TABLE api_keys (
  id          INTEGER PRIMARY KEY,
  user_id     INTEGER NOT NULL REFERENCES users(id),
  org_id      INTEGER NOT NULL REFERENCES organizations(id),
  name        TEXT NOT NULL,
  token_hash  TEXT NOT NULL UNIQUE,
  prefix      TEXT NOT NULL,
  scopes      TEXT NOT NULL DEFAULT '',         -- space-separated
  created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- OAuth2 / OIDC: registered clients and short-lived authorization codes.
CREATE TABLE oauth_clients (
  id             INTEGER PRIMARY KEY,
  client_id      TEXT NOT NULL UNIQUE,
  client_secret  TEXT NOT NULL,
  name           TEXT NOT NULL,
  redirect_uris  TEXT NOT NULL,                 -- space-separated allowlist
  logo_uri       TEXT,
  created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE oauth_codes (
  id                    INTEGER PRIMARY KEY,
  code                  TEXT NOT NULL UNIQUE,
  client_id             TEXT NOT NULL,
  user_id               INTEGER NOT NULL REFERENCES users(id),
  redirect_uri          TEXT NOT NULL,
  scope                 TEXT,
  code_challenge        TEXT,
  code_challenge_method TEXT,
  used                  INTEGER NOT NULL DEFAULT 0,
  expires_at            TEXT NOT NULL,
  created_at            TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Billing orders with a server-enforced state machine:
--   pending -> paid -> fulfilled ; (paid|fulfilled) -> refunded ; pending -> cancelled
-- Addressed by opaque public_id (not the integer PK).
CREATE TABLE orders (
  id             INTEGER PRIMARY KEY,
  public_id      TEXT NOT NULL UNIQUE,
  org_id         INTEGER NOT NULL REFERENCES organizations(id),
  created_by_id  INTEGER NOT NULL REFERENCES users(id),
  kind           TEXT NOT NULL,                 -- 'credit_pack' | 'plan_upgrade'
  amount_cents   INTEGER NOT NULL,
  discount_cents INTEGER NOT NULL DEFAULT 0,
  credits        INTEGER NOT NULL DEFAULT 0,
  target_plan    TEXT,
  coupon_code    TEXT,
  status         TEXT NOT NULL DEFAULT 'pending',
  created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Project file attachments. stored_name is a server-generated random name on
-- disk; filename is the original (display only). Metadata here, bytes on disk.
CREATE TABLE attachments (
  id              INTEGER PRIMARY KEY,
  org_id          INTEGER NOT NULL REFERENCES organizations(id),
  project_id      INTEGER NOT NULL REFERENCES projects(id),
  uploaded_by_id  INTEGER NOT NULL REFERENCES users(id),
  filename        TEXT NOT NULL,
  stored_name     TEXT NOT NULL UNIQUE,
  content_type    TEXT,
  size_bytes      INTEGER NOT NULL,
  created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Outbound webhook subscriptions: the org registers a URL the server POSTs
-- signed event payloads to. `secret` signs OUTBOUND deliveries (HMAC-SHA256).
CREATE TABLE webhooks (
  id             INTEGER PRIMARY KEY,
  org_id         INTEGER NOT NULL REFERENCES organizations(id),
  created_by_id  INTEGER NOT NULL REFERENCES users(id),
  url            TEXT NOT NULL,
  events         TEXT NOT NULL DEFAULT '',     -- space-separated event names
  secret         TEXT NOT NULL,
  active         INTEGER NOT NULL DEFAULT 1,
  created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Idempotency ledger for INBOUND provider webhooks. The secure inbound handler
-- records each provider delivery id here and rejects repeats (anti-replay).
CREATE TABLE webhook_deliveries (
  id           INTEGER PRIMARY KEY,
  delivery_id  TEXT NOT NULL UNIQUE,
  org_id       INTEGER NOT NULL REFERENCES organizations(id),
  event        TEXT NOT NULL,
  received_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================================================
-- Phase B "haystack" - legitimate product surface (correctly secured). These
-- exist to add realistic depth/volume so the vulnerable surface is buried;
-- they are NOT themselves catalogued vulns.
-- ===========================================================================

-- Task labels / tags and their join table.
CREATE TABLE labels (
  id      INTEGER PRIMARY KEY,
  org_id  INTEGER NOT NULL REFERENCES organizations(id),
  name    TEXT NOT NULL,
  color   TEXT NOT NULL DEFAULT 'slate'
);

CREATE TABLE task_labels (
  task_id   INTEGER NOT NULL REFERENCES tasks(id),
  label_id  INTEGER NOT NULL REFERENCES labels(id),
  PRIMARY KEY (task_id, label_id)
);

-- Per-user notifications (the notifications center).
CREATE TABLE notifications (
  id          INTEGER PRIMARY KEY,
  user_id     INTEGER NOT NULL REFERENCES users(id),
  org_id      INTEGER NOT NULL REFERENCES organizations(id),
  kind        TEXT NOT NULL,                 -- 'mention' | 'assignment' | 'comment' | 'system'
  title       TEXT NOT NULL,
  body        TEXT,
  link        TEXT,
  is_read     INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Saved filter/search views (per user).
CREATE TABLE saved_views (
  id          INTEGER PRIMARY KEY,
  user_id     INTEGER NOT NULL REFERENCES users(id),
  org_id      INTEGER NOT NULL REFERENCES organizations(id),
  name        TEXT NOT NULL,
  kind        TEXT NOT NULL,                 -- 'tasks' | 'projects'
  query       TEXT NOT NULL DEFAULT '',      -- serialized filter
  created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
