_ACCOUNTS = [
    ("alice@northwind.test", "Northwind Systems", "Owner"),
    ("charlie@northwind.test", "Northwind Systems", "Member"),
    ("bob@bluepeak.test", "Bluepeak Labs", "Owner"),
    ("diana@bluepeak.test", "Bluepeak Labs", "Member"),
    ("marcus.webb@northwind.test", "Northwind Systems", "Super-admin"),
]
_PASSWORD = "Password1!"
_BAR = "=" * 60


def render_banner(lab, hardened, runtime, web_url, api_url, stop_hint):
    face = ("LAB  (answer-key signals on, /docs open)" if lab
            else "CHALLENGE (no answer-key signals, /docs hidden)")
    hardening = "ON  (secure-by-default)" if hardened else "OFF  (vulnerable by default)"
    out = [
        _BAR,
        "  PROLANE   intentionally vulnerable training target",
        _BAR,
        "  [!] Deliberate security flaws inside. Localhost use only;",
        "      never expose to a network or the public internet.",
        "",
        "  ENVIRONMENT",
        "    Face          " + face,
        "    Hardening     " + hardening,
        "    Runtime       " + runtime,
        "",
        "  ENDPOINTS",
        "    Web app       " + web_url,
        "    API           " + api_url,
    ]
    if lab:
        out.append("    API docs      " + api_url + "/docs")
    out += [
        "",
        "  SEEDED ACCOUNTS            password for all:  " + _PASSWORD,
    ]
    for email, org, role in _ACCOUNTS:
        out.append("    " + email.ljust(28) + org + " / " + role)
    out += [
        "",
        "  Stop:  " + stop_hint,
        _BAR,
    ]
    return "\n".join(out)
