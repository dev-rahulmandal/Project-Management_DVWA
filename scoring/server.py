"""
The scoreboard VIEWER - a small, separate, localhost-only read-only process.

It reads the solve store + the challenge catalog and renders a hidden-until-solved
dashboard: every vuln starts as a locked tile; once the app-side detectors record
it exploited, its tile flips to reveal the challenge and the timestamp. The viewer
NEVER writes, and it is NOT part of the target's surface - run it on its own port.

Run:  python -m uvicorn scoring.server:app --port 8090
Then open http://localhost:8090/
"""
from __future__ import annotations

import html

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from .catalog import load_catalog
from .store import get_solves

# No OpenAPI/docs - this is a private viewer, not an API surface.
app = FastAPI(title="VulnForge scoreboard viewer", docs_url=None, redoc_url=None, openapi_url=None)

_CATEGORY_ORDER = [
    "Access control", "Injection", "SSRF", "Auth & tokens",
    "Business logic", "Client & web", "Misconfiguration", "Other",
]


def _state() -> dict:
    catalog = load_catalog()
    solves = get_solves()
    items = [
        {**c, "solved": c["id"] in solves,
         "solvedAt": solves.get(c["id"], {}).get("first_solved_at")}
        for c in catalog
    ]
    items.sort(key=lambda i: (_CATEGORY_ORDER.index(i["category"]) if i["category"] in _CATEGORY_ORDER else 99, i["id"]))
    return {"total": len(items), "solved": sum(1 for i in items if i["solved"]), "items": items}


@app.get("/state")
def state():
    return JSONResponse(_state())


def _tile(i: dict) -> str:
    if not i["solved"]:
        # Hidden until solved: no title, no category - just a locked slot.
        return '<div class="tile locked"><span class="lock">LOCKED</span><span class="mask">not yet exploited</span></div>'
    tags = [
        '<span class="tag sev">%s</span>' % html.escape(i["severity"]),
        '<span class="tag">%s</span>' % html.escape(i["category"]),
    ]
    if i["owasp"]:
        tags.append('<span class="tag">%s</span>' % html.escape(i["owasp"]))
    if i["origin"]:
        tags.append('<span class="tag">%s</span>' % html.escape(i["origin"]))
    when = html.escape((i["solvedAt"] or "").replace("T", " ").replace("+00:00", " UTC"))
    return (
        '<div class="tile solved"><span class="title">%s</span>'
        '<span class="tags">%s</span>'
        '<span class="when">solved %s</span>'
        '<span class="id">%s</span></div>'
        % (html.escape(i["title"]), "".join(tags), when, html.escape(i["id"]))
    )


_STYLE = """<style>
:root{--bg:#0f172a;--panel:#1e293b;--line:#334155;--text:#e2e8f0;--muted:#94a3b8;--ok:#34d399}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:32px 20px 64px}
h1{margin:0;font-size:24px}
.sub{color:var(--muted);margin:6px 0 0;font-size:14px}
.bar{height:8px;background:var(--panel);border-radius:999px;margin:16px 0 4px;overflow:hidden}
.bar>span{display:block;height:100%;background:var(--ok);width:0}
.count{color:var(--muted);font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px;margin-top:24px}
.tile{border:1px solid var(--line);background:var(--panel);border-radius:10px;padding:14px;min-height:96px;display:flex;flex-direction:column;gap:6px}
.tile.locked{align-items:center;justify-content:center;text-align:center;opacity:.55;border-style:dashed}
.lock{font-size:11px;font-weight:700;letter-spacing:.12em;color:var(--muted)}
.mask{font-size:11px;color:#64748b}
.tile.solved{border-color:#065f46}
.title{font-weight:600;font-size:14px}
.tags{display:flex;flex-wrap:wrap;gap:5px;margin-top:2px}
.tag{font-size:10px;font-weight:600;border-radius:5px;padding:2px 7px;background:#0b1220;color:var(--muted);border:1px solid var(--line)}
.tag.sev{background:#052e2b;color:#5eead4;border-color:#115e59}
.when{font-size:11px;color:var(--ok)}
.id{font-family:ui-monospace,Menlo,monospace;font-size:10px;color:#64748b;margin-top:auto}
</style>"""

_SCRIPT = """<script>
async function poll(){
  try{
    const r=await fetch('/state',{cache:'no-store'});
    const d=await r.json();
    if(d.solved!==window.__solved){location.reload();}
  }catch(e){}
}
setInterval(poll,4000);
</script>"""


@app.get("/", response_class=HTMLResponse)
def dashboard():
    s = _state()
    pct = round(100 * s["solved"] / s["total"]) if s["total"] else 0
    tiles = "".join(_tile(i) for i in s["items"])
    body = (
        '<div class="wrap">'
        '<h1>Scoreboard</h1>'
        '<p class="sub">Vulnerabilities are revealed here as the app detects them being exploited.</p>'
        '<div class="bar"><span style="width:%d%%"></span></div>'
        '<p class="count">%d / %d exploited (%d%%)</p>'
        '<div class="grid">%s</div>'
        '</div>'
        % (pct, s["solved"], s["total"], pct, tiles)
    )
    doc = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Scoreboard</title>' + _STYLE + '</head><body>' + body
        + '<script>window.__solved=%d;</script>' % s["solved"] + _SCRIPT
        + '</body></html>'
    )
    return HTMLResponse(doc)
