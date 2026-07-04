from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import config
from .db import init_db
from .routes.me import router as me_router
from .routes.internal import router as internal_router
from .routes.projects import router as projects_router
from .routes.tasks import router as tasks_router
from .routes.users import router as users_router
from .routes.org import router as org_router
from .routes.attachments import router as attachments_router
from .routes.billing import router as billing_router
from .routes.oauth import router as oauth_router
from .routes.vulns.oauth_vulns import router as oauth_vulns_router
from .routes.vulns.billing_logic import router as billing_logic_router
from .routes.vulns.seat_bypass import router as seat_bypass_router
from .routes.keys import router as keys_router
from .routes.scim import router as scim_router
from .routes.vulns.shadow_integrations import router as shadow_integrations_router
from .routes.webhooks import router as webhooks_router
from .routes.realtime import router as realtime_router
from .routes.dashboard import router as dashboard_router
from .routes.collab import router as collab_router
from .routes.reporting import router as reporting_router
from .routes.decoy_cards import router as decoy_cards_router
from .routes.decoy_readme import router as decoy_readme_router
from .routes.decoy_avatar import router as decoy_avatar_router
from .routes.decoy_prefs import router as decoy_prefs_router
from .routes.admin import router as admin_router
from .routes.vulns.bola import router as bola_router
from .routes.vulns.mass_assignment import router as mass_assignment_router
from .routes.vulns.bfla import router as bfla_router
from .routes.vulns.ssrf import router as ssrf_router
from .routes.vulns.sqli import router as sqli_router
from .routes.vulns.excess_data import router as excess_data_router
from .routes.vulns.open_redirect import router as open_redirect_router
from .routes.vulns.auth_jwt_alg import router as auth_jwt_alg_router
from .routes.vulns.weak_token import router as weak_token_router
from .routes.vulns.race import router as race_router
from .routes.vulns.ssti import router as ssti_router
from .routes.vulns.deserialize import router as deserialize_router
from .routes.vulns.misconfig import router as misconfig_router
from .routes.vulns.resource import router as resource_router
from .routes.vulns.cmdi import router as cmdi_router
from .routes.vulns.pathtraversal import router as pathtraversal_router
from .routes.vulns.cors import router as cors_router
from .routes.vulns.bruteforce import router as bruteforce_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="VulnForge API",
    version="0.1.0",
    description=(
        "Service tier for the VulnForge platform. Bearer-token authenticated; "
        "obtain a token from the web app's session-to-token exchange."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.WEB_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(me_router)
app.include_router(internal_router)
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(users_router)
app.include_router(org_router)
app.include_router(attachments_router)
app.include_router(billing_router)
app.include_router(oauth_router)
app.include_router(oauth_vulns_router)
app.include_router(billing_logic_router)
app.include_router(seat_bypass_router)
app.include_router(keys_router)
app.include_router(scim_router)
app.include_router(shadow_integrations_router)
app.include_router(webhooks_router)
app.include_router(realtime_router)
app.include_router(dashboard_router)
app.include_router(collab_router)
app.include_router(reporting_router)
# Decoys (Phase C C4) - look-vulnerable-but-correctly-secured noise.
app.include_router(decoy_cards_router)
app.include_router(decoy_readme_router)
app.include_router(decoy_avatar_router)
app.include_router(decoy_prefs_router)
app.include_router(admin_router)
# sqli_router's literal "/api/projects/search" must register BEFORE bola_router's
# parametric "/api/projects/{project_id}", or the latter shadows it (422 on int parse).
app.include_router(sqli_router)
app.include_router(bola_router)
app.include_router(mass_assignment_router)
app.include_router(bfla_router)
app.include_router(ssrf_router)
app.include_router(excess_data_router)
app.include_router(open_redirect_router)
app.include_router(auth_jwt_alg_router)
app.include_router(weak_token_router)
app.include_router(race_router)
app.include_router(ssti_router)
app.include_router(deserialize_router)
app.include_router(misconfig_router)
app.include_router(resource_router)
app.include_router(cmdi_router)
app.include_router(pathtraversal_router)
app.include_router(cors_router)
app.include_router(bruteforce_router)
