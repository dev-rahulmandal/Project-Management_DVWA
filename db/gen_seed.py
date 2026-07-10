"""
Deterministic generator for the Phase-B "haystack" bulk seed.

Emits db/seed_bulk.sql - a large volume of LEGITIMATE, correctly-secured product
data (orgs/users/projects/tasks/comments/activity/labels/notifications/saved
views/orders) so the vulnerable surface is buried in realistic noise.

The FIXTURE CORE (orgs 1-2, users 1-5, projects 1-6, tasks 1-6, coupons, the demo
oauth client, the seeded invitation/comments/audit rows) lives in seed.sql and is
NEVER touched here - the 35-vuln answer-key depends on those exact ids. Bulk ids
start past the fixture (orgs 3+, users 6+, projects 7+, tasks 7+).

Reproducible: fixed RNG seed + fixed date anchor -> identical output every run, so
`make verify` stays deterministic. Run:  python db/gen_seed.py
"""
import hashlib
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(1337)
ANCHOR = datetime(2026, 6, 20)
PW = "$2b$12$bpwMRSLMArdyTjtVjP2BBOY7u58y7ydIxX5ZulhTNlzYi7dwzgut6"  # bcrypt("Password1!")


def esc(s):
    return "NULL" if s is None else "'" + str(s).replace("'", "''") + "'"


def days_ago(n):
    return (ANCHOR - timedelta(days=n)).strftime("%Y-%m-%dT%H:%M:%S")


def rows(table, cols, data):
    if not data:
        return ""
    out = [f"INSERT INTO {table} ({', '.join(cols)}) VALUES"]
    lines = []
    for r in data:
        vals = ", ".join(str(v) if isinstance(v, int) else esc(v) for v in r)
        lines.append(f"  ({vals})")
    return out[0] + "\n" + ",\n".join(lines) + ";\n\n"


FIRST = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
         "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
         "Thomas", "Sarah", "Chris", "Karen", "Daniel", "Nancy", "Matthew", "Lisa", "Anthony",
         "Betty", "Mark", "Sandra", "Paul", "Ashley", "Steven", "Kim", "Andrew", "Emily",
         "Kevin", "Donna", "Brian", "Michelle", "George", "Carol", "Edward", "Amanda"]
LAST = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
        "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young"]

NEW_ORGS = [  # (id, name, slug, plan)
    (3, "Meridian Retail", "meridian", "pro"),
    (4, "Larkfield Media", "larkfield", "enterprise"),
    (5, "Cascade Freight", "cascade", "starter"),
    (6, "Halcyon Health", "halcyon", "enterprise"),
    (7, "Vantage Robotics", "vantage", "pro"),
    (8, "Delmont Foods", "delmont", "starter"),
]
ORG_SLUG = {1: "northwind", 2: "bluepeak", **{o[0]: o[2] for o in NEW_ORGS}}
ALL_ORGS = [1, 2] + [o[0] for o in NEW_ORGS]

PROJ_WORDS = ["Platform", "Migration", "Redesign", "Analytics", "Onboarding", "Billing",
              "Compliance", "Mobile", "Infrastructure", "Search", "Notifications", "Reporting",
              "Integration", "Marketing Site", "Data Lake", "API v2", "Checkout", "Dashboard",
              "Identity", "Localization", "Performance", "Support Portal", "Pricing", "Webhooks"]
PROJ_PREFIX = ["", "Q1 ", "Q2 ", "Q3 ", "Q4 ", "Internal ", "Customer ", "Legacy ", "New "]
PROJ_DESC = ["Cross-team initiative tracked for this quarter.",
             "Owned by the platform team; high priority.",
             "Migrating off the legacy stack incrementally.",
             "Customer-requested; tied to a renewal.",
             "Internal tooling to reduce manual ops.",
             "Compliance-driven; deadline is firm.",
             "Experimental - may be cut next planning cycle."]
TASK_VERBS = ["Implement", "Design", "Review", "Fix", "Refactor", "Document", "Test", "Deploy",
              "Investigate", "Migrate", "Audit", "Spike", "Wire up", "Polish", "Triage"]
TASK_NOUNS = ["the login flow", "the export job", "rate limiting", "the settings page",
              "the search index", "pagination", "the webhook retries", "the billing cron",
              "the role checks", "the email templates", "the CSV importer", "the API docs",
              "the onboarding wizard", "the dashboard charts", "the audit log viewer",
              "the notification badges", "the bulk-edit modal", "the dark mode styles"]
TASK_BODY = ["Acceptance criteria in the linked doc.", "Blocked on design sign-off.",
             "Should be a quick one.", "Needs a follow-up with the data team.",
             "See the thread in #eng.", "Carry-over from last sprint.",
             "Coordinate with QA before merging.", "Low risk; ship behind a flag."]
COMMENTS = ["Looks good to me.", "Can you add a test for the edge case?",
            "I'll pick this up tomorrow.", "Pushed a fix - please re-review.",
            "Do we have a design for this yet?", "This is blocked until the migration lands.",
            "Nice, that's much cleaner.", "Let's split this into two tasks.",
            "Bumping priority - customer is waiting.", "Done, moving to review."]
LABEL_POOL = [("bug", "red"), ("feature", "green"), ("chore", "slate"), ("urgent", "amber"),
              ("backend", "blue"), ("frontend", "violet"), ("design", "pink"), ("docs", "cyan"),
              ("blocked", "orange"), ("good-first-issue", "teal")]
STATUS = ["open", "open", "in_progress", "in_progress", "done", "done", "done"]
PRIO = ["low", "medium", "medium", "high", "high"]
ACTIONS = ["project.create", "task.create", "task.update", "task.assign", "comment.add",
           "member.invite", "settings.update", "label.create", "project.archive"]

out = ["-- GENERATED by db/gen_seed.py - do not edit by hand. Deterministic (seed 1337).",
       "-- Phase-B haystack: legitimate, correctly-secured product volume.",
       "PRAGMA foreign_keys = ON;", ""]

# ---- organizations ----
org_rows = [(o[0], o[1], o[2], o[3], random.choice([0, 0, 250, 1000, 5000])) for o in NEW_ORGS]
out.append(rows("organizations", ["id", "name", "slug", "plan_tier", "credit_balance"], org_rows))

# ---- users (extra for fixture orgs + full sets for new orgs) ----
uid = 6
users = []                       # (id, org_id, role)
org_users = {o: [] for o in ALL_ORGS}
org_users[1] = [1, 2, 5]         # existing northwind
org_users[2] = [3, 4]            # existing bluepeak
user_rows = []
plan_extra = {1: 4, 2: 4}        # extra users for fixture orgs
for o in ALL_ORGS:
    if o in (1, 2):
        n = plan_extra[o]
        roles = ["admin"] + ["member"] * (n - 1)
    else:
        n = random.randint(4, 6)
        roles = ["owner", "admin"] + ["member"] * (n - 2)
    for role in roles:
        fn, ln = random.choice(FIRST), random.choice(LAST)
        email = f"{fn.lower()}.{ln.lower()}{uid}@{ORG_SLUG[o]}.test"
        note = random.choice([None, None, None, "Champion user.", "Trial - follow up.", "Power user."])
        user_rows.append((uid, o, email, f"{fn} {ln}", role, 0, PW, note))
        org_users[o].append(uid)
        uid += 1
out.append(rows("users",
                ["id", "org_id", "email", "full_name", "role", "is_super_admin", "password_hash", "internal_notes"],
                user_rows))

# ---- labels (per org) ----
lid = 1
labels = {o: [] for o in ALL_ORGS}
label_rows = []
for o in ALL_ORGS:
    for name, color in random.sample(LABEL_POOL, random.randint(5, 7)):
        label_rows.append((lid, o, name, color))
        labels[o].append(lid)
        lid += 1
out.append(rows("labels", ["id", "org_id", "name", "color"], label_rows))

# ---- projects (extra for all orgs; bulk ids from 7) ----
pid = 7
projects = {o: [] for o in ALL_ORGS}
projects[1] = [1, 2, 3]
projects[2] = [4, 5, 6]
proj_rows = []
for o in ALL_ORGS:
    for _ in range(random.randint(8, 12)):
        name = (random.choice(PROJ_PREFIX) + random.choice(PROJ_WORDS)).strip()
        st = random.choice(["active"] * 6 + ["archived"] * 2)
        deleted = days_ago(random.randint(1, 40)) if random.random() < 0.06 else None
        creator = random.choice(org_users[o])
        proj_rows.append((pid, o, name, random.choice(PROJ_DESC), st, creator, deleted,
                          days_ago(random.randint(30, 400))))
        projects[o].append(pid)
        pid += 1
out.append(rows("projects",
                ["id", "org_id", "name", "description", "status", "created_by_id", "deleted_at", "created_at"],
                proj_rows))

# ---- tasks (for every project; bulk ids from 7) ----
tid = 7
task_rows = []
tasks_by_org = {o: [] for o in ALL_ORGS}
for o in ALL_ORGS:
    for p in projects[o]:
        if p <= 6:
            continue  # fixture projects keep their fixture tasks; add bulk only to bulk projects
        for _ in range(random.randint(3, 8)):
            title = f"{random.choice(TASK_VERBS)} {random.choice(TASK_NOUNS)}"
            assignee = random.choice(org_users[o])
            due = days_ago(random.randint(-30, 20)) if random.random() < 0.4 else None
            task_rows.append((tid, p, o, title, random.choice(TASK_BODY), assignee,
                              random.choice(STATUS), random.choice(PRIO),
                              due[:10] if due else None, days_ago(random.randint(1, 380))))
            tasks_by_org[o].append(tid)
            tid += 1
out.append(rows("tasks",
                ["id", "project_id", "org_id", "title", "body", "assignee_id", "status", "priority", "due_date", "created_at"],
                task_rows))

# ---- task_labels ----
tl_rows = []
seen = set()
for o in ALL_ORGS:
    for t in tasks_by_org[o]:
        for _ in range(random.randint(0, 2)):
            if labels[o]:
                lb = random.choice(labels[o])
                if (t, lb) not in seen:
                    seen.add((t, lb))
                    tl_rows.append((t, lb))
out.append(rows("task_labels", ["task_id", "label_id"], tl_rows))

# ---- comments ----
com_rows = []
for o in ALL_ORGS:
    for t in tasks_by_org[o]:
        for _ in range(random.randint(0, 3)):
            com_rows.append((t, o, random.choice(org_users[o]), random.choice(COMMENTS),
                             days_ago(random.randint(0, 200))))
out.append(rows("comments", ["task_id", "org_id", "author_id", "body", "created_at"], com_rows))

# ---- activity (audit_logs) ----
act_rows = []
for o in ALL_ORGS:
    for p in projects[o]:
        for _ in range(random.randint(2, 4)):
            act_rows.append((o, random.choice(org_users[o]), random.choice(ACTIONS),
                             "project", p, f"198.51.100.{random.randint(2, 250)}",
                             days_ago(random.randint(0, 300))))
out.append(rows("audit_logs",
                ["org_id", "user_id", "action", "resource_type", "resource_id", "ip", "created_at"],
                act_rows))

# ---- notifications (per user) ----
NOTIF = [("assignment", "You were assigned a task"), ("mention", "You were mentioned in a comment"),
         ("comment", "New comment on your task"), ("system", "Weekly digest is ready")]
notif_rows = []
for o in ALL_ORGS:
    for u in org_users[o]:
        for _ in range(random.randint(4, 12)):
            kind, title = random.choice(NOTIF)
            notif_rows.append((u, o, kind, title, random.choice(COMMENTS),
                               "/tasks", 1 if random.random() < 0.5 else 0,
                               days_ago(random.randint(0, 60))))
out.append(rows("notifications",
                ["user_id", "org_id", "kind", "title", "body", "link", "is_read", "created_at"],
                notif_rows))

# ---- saved_views (per user) ----
VIEWS = [("My open tasks", "tasks", "status=open&assignee=me"),
         ("High priority", "tasks", "priority=high"),
         ("Active projects", "projects", "status=active"),
         ("Recently updated", "tasks", "sort=updated"),
         ("Blocked", "tasks", "label=blocked")]
sv_rows = []
for o in ALL_ORGS:
    for u in org_users[o]:
        for name, kind, q in random.sample(VIEWS, random.randint(1, 3)):
            sv_rows.append((u, o, name, kind, q, days_ago(random.randint(0, 120))))
out.append(rows("saved_views", ["user_id", "org_id", "name", "kind", "query", "created_at"], sv_rows))

# ---- orders (billing/transaction ledger, per org) ----
order_rows = []
on = 0
for o in ALL_ORGS:
    for _ in range(random.randint(2, 5)):
        on += 1
        kind = random.choice(["credit_pack", "plan_upgrade"])
        amt = random.choice([900, 3900, 9900, 19900])
        order_rows.append((f"ord_seed_{on:04d}", o, random.choice(org_users[o]), kind, amt, 0,
                           amt // 9 if kind == "credit_pack" else 0,
                           "pro" if kind == "plan_upgrade" else None, None,
                           random.choice(["paid", "fulfilled", "refunded", "pending"]),
                           days_ago(random.randint(1, 300))))
out.append(rows("orders",
                ["public_id", "org_id", "created_by_id", "kind", "amount_cents", "discount_cents",
                 "credits", "target_plan", "coupon_code", "status", "created_at"], order_rows))

# ---- attachments (files on a subset of projects). seed_bulk carries only the
#      METADATA; api/db.py materializes matching placeholder bytes on disk at
#      seed time so the seeded files download like real ones. ----
ATT_FILES = [
    ("Q3-roadmap.pdf", "application/pdf"),
    ("design-spec.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("budget-forecast.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("wireframes.png", "image/png"),
    ("meeting-notes.md", "text/markdown"),
    ("customer-export.csv", "text/csv"),
    ("architecture-overview.pdf", "application/pdf"),
    ("brand-assets.zip", "application/zip"),
    ("api-contract.json", "application/json"),
    ("release-checklist.md", "text/markdown"),
]
HEX = "0123456789abcdef"
FORCED_ATT = {1, 4}   # the showcase projects always carry files
att_rows = []
aid = 1
for o in ALL_ORGS:
    for p in projects[o]:
        if p in FORCED_ATT or random.random() < 0.4:
            for _ in range(random.randint(1, 3)):
                fn, ct = random.choice(ATT_FILES)
                ext = "." + fn.rsplit(".", 1)[1]
                stored = "".join(random.choice(HEX) for _ in range(32)) + ext
                size = random.randint(2, 90) * 1024 + random.randint(0, 1023)
                up = random.choice(org_users[o])
                att_rows.append((aid, o, p, up, fn, stored, ct, size, days_ago(random.randint(1, 220))))
                aid += 1
out.append(rows("attachments",
                ["id", "org_id", "project_id", "uploaded_by_id", "filename", "stored_name",
                 "content_type", "size_bytes", "created_at"], att_rows))

# ---- webhooks (outbound subscriptions). Inert `.example` hosts (reserved TLD,
#      does not resolve) so a "test delivery" never reaches a live endpoint. ----
WH_HOSTS = ["hooks.{s}.example", "events.{s}.example", "ingest.pipeline.example",
            "api.crm-connector.example", "notify.opsdesk.example"]
WH_PATHS = ["/prolane/inbound", "/webhooks/prolane", "/v1/events", "/hooks/incoming"]
WH_EVENTS = ["order.paid", "task.created", "member.invited"]
URLSAFE = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
wh_rows = []
wid = 1
for o in ALL_ORGS:
    for _ in range(random.randint(2, 3) if o in (1, 2) else random.randint(1, 3)):
        host = random.choice(WH_HOSTS).format(s=ORG_SLUG[o])
        url = "https://" + host + random.choice(WH_PATHS)
        events = " ".join(sorted(random.sample(WH_EVENTS, random.randint(1, 3))))
        secret = "whk_" + "".join(random.choice(URLSAFE) for _ in range(32))
        creator = random.choice(org_users[o])
        active = 1 if random.random() < 0.8 else 0
        wh_rows.append((wid, o, creator, url, events, secret, active, days_ago(random.randint(3, 260))))
        wid += 1
out.append(rows("webhooks",
                ["id", "org_id", "created_by_id", "url", "events", "secret", "active", "created_at"],
                wh_rows))

# ---- api_keys (personal access tokens). Only the sha-256 hash + prefix are
#      stored, exactly like the live create path - the plaintext never exists. ----
PAT_NAMES = ["CI pipeline", "Production backup", "Zapier integration", "Local dev laptop",
             "Terraform", "Data warehouse sync", "Uptime monitor", "Mobile build", "Analytics ETL"]
SCOPE_SETS = [
    ["profile:read"],
    ["projects:read", "tasks:read"],
    ["projects:read", "projects:write", "tasks:read", "tasks:write"],
    ["projects:read"],
    ["tasks:read", "tasks:write"],
    ["projects:read", "tasks:read", "profile:read"],
]
ak_rows = []
kid = 1
for o in ALL_ORGS:
    if o in (1, 2):
        # guarantee every fixture account has a token (developer page is per-user)
        targets = list(org_users[o]) + [random.choice(org_users[o]) for _ in range(random.randint(1, 2))]
    else:
        targets = [random.choice(org_users[o]) for _ in range(random.randint(1, 3))]
    for u in targets:
        name = random.choice(PAT_NAMES)
        fake = "vfpat_" + "".join(random.choice(URLSAFE) for _ in range(32))
        thash = hashlib.sha256(fake.encode()).hexdigest()
        prefix = fake[:14]
        scopes = " ".join(random.choice(SCOPE_SETS))
        ak_rows.append((kid, u, o, name, thash, prefix, scopes, days_ago(random.randint(2, 300))))
        kid += 1
out.append(rows("api_keys",
                ["id", "user_id", "org_id", "name", "token_hash", "prefix", "scopes", "created_at"],
                ak_rows))

text = "\n".join(out)
Path(__file__).parent.joinpath("seed_bulk.sql").write_text(text, encoding="utf-8")

# Summary for the operator.
def n(rws):
    return sum(r.count("\n  (") for r in rws)
print("seed_bulk.sql written:")
print(f"  orgs(+{len(org_rows)})  users(+{len(user_rows)})  labels({len(label_rows)})  "
      f"projects(+{len(proj_rows)})  tasks(+{len(task_rows)})")
print(f"  task_labels({len(tl_rows)})  comments({len(com_rows)})  activity({len(act_rows)})  "
      f"notifications({len(notif_rows)})  saved_views({len(sv_rows)})  orders({len(order_rows)})")
print(f"  attachments({len(att_rows)})  webhooks({len(wh_rows)})  api_keys({len(ak_rows)})")
