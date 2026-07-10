-- Prolane deterministic seed - SQLite (dev).
-- All accounts use password: Password1!
-- Hashes: bcrypt cost 12 (fake training data only).

PRAGMA foreign_keys = ON;

INSERT INTO organizations (id, name, slug, plan_tier) VALUES
  (1, 'Northwind Systems', 'northwind', 'pro'),
  (2, 'Bluepeak Labs',     'bluepeak',  'starter');

-- Users: org 1 ids 1-2 + platform-ops id 5 | org 2 ids 3-4
INSERT INTO users (id, org_id, email, full_name, role, is_super_admin, password_hash, internal_notes) VALUES
  (1, 1, 'alice@northwind.test',       'Alice Forrest', 'owner',  0, '$2b$12$bpwMRSLMArdyTjtVjP2BBOY7u58y7ydIxX5ZulhTNlzYi7dwzgut6', 'Upgraded to Pro in Q1; expansion likely at renewal.'),
  (2, 1, 'charlie@northwind.test',     'Charlie Dunn',  'member', 0, '$2b$12$pgYdCyAchuhh9M6RuWFNm.q6XEJZtF44OswHPW/6iHCystVQKmd.m', NULL),
  (3, 2, 'bob@bluepeak.test',          'Bob Hale',      'owner',  0, '$2b$12$nMq92KWvZ1h8JvOtaubRvu2RGiIRnSOq12495beDVmsS/uTcUgRRG',  'Migrated from a competitor in March.'),
  (4, 2, 'diana@bluepeak.test',        'Diana Marsh',   'member', 0, '$2b$12$6VsOG.feapMJ4mnsJsMYJei9FPe/zcKXKnOhvx324s/FRaPd4WAlC',  NULL),
  (5, 1, 'marcus.webb@northwind.test', 'Marcus Webb',   'owner',  1, '$2b$12$Yx34OfLjS5v0Cy4FfLWviOQfAGSkqGpDFWH6Q4/Ety.DXVwm2knWK',  'Platform operations; owns billing and provisioning.');

-- Projects: org 1 ids 1-3, org 2 ids 4-6
INSERT INTO projects (id, org_id, name, description, status, created_by_id) VALUES
  (1, 1, 'Website Redesign',   'Overhaul the marketing site',     'active',   1),
  (2, 1, 'API Integration',    'Connect to Stripe and SendGrid',  'active',   1),
  (3, 1, 'Q3 Roadmap',         'Internal planning document',      'archived', 2),
  (4, 2, 'Data Pipeline',      'ETL for customer analytics',      'active',   3),
  (5, 2, 'Security Audit',     'Prep for SOC 2 certification',    'active',   3),
  (6, 2, 'Mobile App',         'iOS and Android clients',         'active',   4);

-- Tasks: sequential IDs across orgs
INSERT INTO tasks (id, project_id, org_id, title, body, assignee_id, status, priority) VALUES
  (1, 1, 1, 'Design mockups',     'Figma link: internal.northwind.test/designs', 2, 'done',        'high'),
  (2, 1, 1, 'Copy review',        'Due end of sprint.',                     1, 'in_progress', 'medium'),
  (3, 2, 1, 'OAuth setup',        'Use PKCE flow per RFC 7636.',            1, 'open',        'high'),
  (4, 4, 2, 'Schema design',      'Star schema preferred for analytics.',   4, 'in_progress', 'high'),
  (5, 5, 2, 'Vendor security questionnaire', 'Draft by end of month.',       3, 'open',        'medium'),
  (6, 6, 2, 'Android wireframes', 'Share with design team first.',          4, 'open',        'low');

-- Audit log: admin-only history (surface for API-BFLA-001). Org-scoped.
INSERT INTO audit_logs (org_id, user_id, action, resource_type, resource_id, ip) VALUES
  (1, 1, 'project.create',  'project', 1, '198.51.100.10'),
  (1, 1, 'user.invite',     'user',    2, '198.51.100.10'),
  (1, 2, 'task.update',     'task',    2, '198.51.100.23'),
  (2, 3, 'project.create',  'project', 4, '203.0.113.7'),
  (2, 3, 'settings.update', 'org',     2, '203.0.113.7');

-- Coupons: single-use redeem targets (race vuln) + a billing discount code.
INSERT INTO coupons (code, remaining_uses, discount_pct) VALUES
  ('WELCOME50',    1, 0),
  ('SPRING24',     1, 0),
  ('SAVE20',       5, 20);

-- A registered OAuth client ("Connect with Prolane" integration).
INSERT INTO oauth_clients (client_id, client_secret, name, redirect_uris, logo_uri) VALUES
  ('demo-integration', 'cs_demo_3f9a1c7b', 'Demo Integration',
   'https://demo.example/callback http://localhost:9000/cb', NULL);

-- A pending invitation (Northwind), so the members admin shows realistic data.
INSERT INTO invitations (org_id, email, role, token, expires_at) VALUES
  (1, 'newbie@northwind.test', 'member', 'inv_seed_northwind_pending_001', '2031-01-01T00:00:00');

-- Due dates on a couple of tasks.
UPDATE tasks SET due_date = '2026-07-15' WHERE id = 2;
UPDATE tasks SET due_date = '2026-06-30' WHERE id = 3;

-- Seeded task comments (Northwind task 1).
INSERT INTO comments (task_id, org_id, author_id, body) VALUES
  (1, 1, 1, 'Mockups look great - ready to hand off to engineering.'),
  (1, 1, 2, 'One tweak on the hero spacing and we are good.');
