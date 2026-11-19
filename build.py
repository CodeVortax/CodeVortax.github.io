#!/usr/bin/env python3
"""Generate the site from data/projects/*.json.

    python3 build.py

Writes:
  index.html      the landing page, cards pointing at the local pages
  projects.html   a plain index of every page, for search engines and no-JS
  projects/<slug>.html  one page per project

The CSS and JS are hand-written and are not touched here.
"""

import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data" / "projects"
OUT = ROOT / "projects"

CAT_LABELS = {
    "android": "Android",
    "esp32": "ESP32",
    "tool": "CLI &amp; tools",
    "web": "Web",
}

STATUS_LABELS = {
    "beta": "beta",
    "stable": "stable",
    "app": "app",
    "module": "Magisk module",
    "research": "research notes",
}

# Short blurbs for the landing page cards, one line each.
CARD_BLURBS = {
    "focus": "Study first, then spend what you earn. Gates Shorts, Reels and distracting apps until your daily work is done.",
    "crystal-alarm": "A private alarm clock: analog clock face, timer, stopwatch, puzzle dismiss and volume ramp. No internet permission.",
    "swipe-tally": "Counts Shorts, Reels and TikTok swipes correctly with an AccessibilityService. About 600 lines of plain Kotlin.",
    "esp-usb-bridge": "Shares the phone's USB port with Termux as a serial-over-network port, so esptool just works. No root, no PC.",
    "appblocker": "Magisk module that blocks or disables apps from a list, plus a local web UI to manage everything.",
    "esp32-ir-bench": "Learns IR codes from a real remote and fires them back through an IR LED, with a phone-friendly web app served by the chip.",
    "esp32-wifi-repeater-manage": "ESP32 repeater that counts data per device, enforces a daily quota, and gives you a live dashboard and a Telegram bot.",
    "vortax": "Run and manage QEMU virtual machines from one small CLI and a web dashboard. Standard library only, KVM or software.",
    "relink": "Downloader for sites that only hand out temporary links: it remembers how to get a fresh one and resumes where it stopped.",
    "rtlterm": "Arabic, Persian, Urdu and Hebrew in terminals that can't join or reverse text, like Termux. Pure Python, no dependencies.",
    "qpack": "Scans photos of exams and homework, deskews the pages, runs OCR and grades the answers, with an Arabic physics grader.",
    "unisoc-imei-notes": "Where Unisoc phones keep IMEI, serial and MAC addresses, and how the tools read or write them. Plus restoration tooling.",
    "twrp-theme-studio": "Visual, live-preview editor for TWRP recovery themes: load a real ui.xml, edit it by tapping, export a flash-ready zip.",
}

JSON_LD_EXTRA = {}

HEAD = """<!doctype html>
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#0b0f17">
<meta name="color-scheme" content="dark">
<link rel="canonical" href="https://codevortax.github.io/{path}">

<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://codevortax.github.io/{path}">
<meta name="twitter:card" content="summary_large_image">

<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%230b0f17'/%3E%3Cpath d='M40 20 26 32l14 12' fill='none' stroke='%2358a6ff' stroke-width='6' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
<link rel="stylesheet" href="{css}">
<script>document.documentElement.classList.replace('no-js','js');</script>
{extra}</head>
<body>
"""

NAV = """
<a class="skip" href="#main">Skip to content</a>
<div class="progress"><span id="bar"></span></div>

<header class="nav">
  <a class="brand" href="{home}">
    <span class="brand-mark" aria-hidden="true">&lt;</span>CodeVortax<span class="brand-mark" aria-hidden="true">&gt;</span>
  </a>
  <nav aria-label="Sections">
    <a href="{home}#projects">Projects</a>
    <a href="{home}#about">About</a>
    <a class="gh" href="https://github.com/CodeVortax">GitHub <span aria-hidden="true">↗</span></a>
  </nav>
</header>
"""

FOOT = """
<footer>
  <p class="foot-links">
    <a href="{home}#projects">All projects</a>
    <span aria-hidden="true">·</span>
    <a href="{repo}">Source on GitHub</a>
    <span aria-hidden="true">·</span>
    <a href="https://github.com/CodeVortax/CodeVortax.github.io">This site's source</a>
  </p>
  <p class="foot-copy">&copy; <span id="year">2026</span> CodeVortax</p>
</footer>

<script src="{js}" defer></script>
</body>
</html>
"""


def esc(text):
    """Escape a plain string, leaving the small amount of inline HTML we author."""
    return text


def load():
    projects = []
    for path in sorted(DATA.glob("*.json")):
        with path.open(encoding="utf-8") as fh:
            projects.append(json.load(fh))
    projects.sort(key=lambda p: p["order"])
    return projects


def meta_row(label, value):
    return (
        '        <div class="dl-row">\n'
        f'          <dt>{label}</dt>\n'
        f'          <dd>{value}</dd>\n'
        "        </div>\n"
    )


def feature_item(pair):
    name, body = pair
    return (
        '        <li class="feature reveal">\n'
        f'          <h3>{name}</h3>\n'
        f'          <p>{body}</p>\n'
        "        </li>\n"
    )


def install_step(step, index):
    # the badge already shows the number, so drop a leading "1. " from the title
    title = re.sub(r"^\s*\d+[.)]\s*", "", step["title"])
    out = ['        <li class="step reveal">\n']
    out.append(f'          <span class="step-n" aria-hidden="true">{index}</span>\n')
    out.append('          <div class="step-body">\n')
    out.append(f'            <h3>{title}</h3>\n')
    if "body" in step:
        out.append(f'            <p>{step["body"]}</p>\n')
    if "code" in step:
        code = html.escape(step["code"])
        out.append(
            '            <div class="codewrap">'
            '<button class="copy" type="button" aria-label="Copy this command">Copy</button>'
            f"<pre><code>{code}</code></pre></div>\n"
        )
    out.append("          </div>\n")
    out.append("        </li>\n")
    return "".join(out)


def table_block(table):
    head = "".join(f"<th scope=\"col\">{c}</th>" for c in table["cols"])
    rows = ""
    for row in table["rows"]:
        cells = "".join(f"<td>{c}</td>" for c in row)
        rows += f"            <tr>{cells}</tr>\n"
    return (
        '      <div class="table-block reveal">\n'
        f'        <h2 class="sub">{table["title"]}</h2>\n'
        '        <div class="table-scroll">\n'
        "          <table>\n"
        f"            <thead><tr>{head}</tr></thead>\n"
        "            <tbody>\n"
        f"{rows}"
        "            </tbody>\n"
        "          </table>\n"
        "        </div>\n"
        "      </div>\n"
    )


def project_page(p, prev_p, next_p):
    slug = p["slug"]
    title = f'{p["name"]} — CodeVortax'
    desc = re.sub("<[^>]+>", "", p["tagline"])
    desc = html.unescape(desc)

    body = [HEAD.format(
        title=html.escape(title),
        desc=html.escape(desc),
        path=f"projects/{slug}.html",
        css="../style.css",
        extra="",
    )]
    body.append(NAV.format(home="../index.html"))
    body.append('\n<main id="main">\n')

    # header
    body.append('  <article>\n')
    body.append('    <header class="phead">\n      <div class="phead-inner">\n')
    body.append(
        f'        <p class="crumb reveal"><a href="../index.html#projects">Projects</a>'
        f' <span aria-hidden="true">/</span> {CAT_LABELS[p["cat"]]}</p>\n'
    )
    body.append(f'        <h1 class="reveal">{p["name"]}</h1>\n')
    body.append(f'        <p class="ptag reveal">{p["tagline"]}</p>\n')

    chips = [
        f'<span class="tag lang"><i style="--c:{p["color"]}"></i>{p["lang"]}</span>',
        f'<span class="tag">{p["license"]}</span>',
        f'<span class="tag">★ {p["stars"]}</span>',
        f'<span class="tag">{STATUS_LABELS.get(p["status"], p["status"])}</span>',
        f'<span class="tag">{CAT_LABELS[p["cat"]]}</span>',
    ]
    body.append(
        '        <div class="tags reveal">' + "".join(chips) + "</div>\n"
    )
    body.append(
        '        <div class="pcta reveal">\n'
        f'          <a class="btn primary" href="{p["repo"]}">View the source</a>\n'
    )
    if p.get("docs"):
        body.append(
            f'          <a class="btn ghost" href="{p["repo"]}/tree/{p["branch"]}/{p["docs"]}">Documentation</a>\n'
        )
    body.append("        </div>\n")
    body.append("      </div>\n    </header>\n")

    # intro + specs
    body.append('    <div class="pwrap">\n')
    body.append('      <div class="pbody">\n')
    body.append('        <section class="pintro reveal">\n')
    for para in p["intro"]:
        body.append(f"          <p>{para}</p>\n")
    body.append("        </section>\n")

    # features
    if p.get("features"):
        body.append('\n        <section class="psec">\n')
        body.append('          <h2 class="sub reveal">What it does</h2>\n')
        body.append('          <ul class="features">\n')
        for pair in p["features"]:
            body.append(feature_item(pair))
        body.append("          </ul>\n")
        body.append("        </section>\n")
    body.append("      </div>\n")

    # sidebar specs
    body.append('      <aside class="pside reveal">\n')
    body.append('        <div class="specs">\n')
    body.append('          <h2 class="sub">At a glance</h2>\n')
    body.append("          <dl>\n")
    for label, value in p.get("specs", []):
        body.append(meta_row(label, value))
    body.append("          </dl>\n")
    body.append("        </div>\n")
    body.append('        <a class="side-link" href="%s">Repository <span aria-hidden="true">↗</span></a>\n' % p["repo"])
    body.append("      </aside>\n")
    body.append("    </div>\n")

    # install
    if p.get("install"):
        body.append('\n    <section class="pwrap-single">\n')
        body.append('      <div class="psec">\n')
        body.append('        <h2 class="sub reveal">Install</h2>\n')
        body.append('        <ol class="steps">\n')
        for i, step in enumerate(p["install"], 1):
            body.append(install_step(step, i))
        body.append("        </ol>\n")
        body.append("      </div>\n")
        body.append("    </section>\n")

    # usage
    if p.get("usage"):
        body.append('\n    <section class="pwrap-single">\n')
        body.append('      <div class="psec">\n')
        body.append('        <h2 class="sub reveal">How to use it</h2>\n')
        body.append('        <div class="usage">\n')
        for block in p["usage"]:
            body.append('          <div class="usage-block reveal">\n')
            body.append(f'            <h3>{block["title"]}</h3>\n')
            if "body" in block:
                body.append(f'            <p>{block["body"]}</p>\n')
            if "code" in block:
                code = html.escape(block["code"])
                body.append(
                    '            <div class="codewrap">'
                    '<button class="copy" type="button" aria-label="Copy this command">Copy</button>'
                    f"<pre><code>{code}</code></pre></div>\n"
                )
            body.append("          </div>\n")
        body.append("        </div>\n")
        body.append("      </div>\n")
        body.append("    </section>\n")

    # optional table (wiring, telegram commands)
    if p.get("table"):
        body.append('\n    <section class="pwrap-single">\n')
        body.append(table_block(p["table"]))
        body.append("    </section>\n")

    # notes
    if p.get("notes"):
        body.append('\n    <section class="pwrap-single">\n')
        body.append('      <div class="psec">\n')
        body.append('        <h2 class="sub reveal">Good to know</h2>\n')
        body.append('        <ul class="notes">\n')
        for note in p["notes"]:
            body.append(f'          <li class="reveal">{note}</li>\n')
        body.append("        </ul>\n")
        body.append("      </div>\n")
        body.append("    </section>\n")

    # prev / next
    body.append('\n    <nav class="pn" aria-label="More projects">\n')
    if prev_p:
        body.append(
            f'      <a class="pn-link prev" href="{prev_p["slug"]}.html">'
            f'<span>Previous</span><b>{prev_p["name"]}</b></a>\n'
        )
    if next_p:
        body.append(
            f'      <a class="pn-link next" href="{next_p["slug"]}.html">'
            f'<span>Next</span><b>{next_p["name"]}</b></a>\n'
        )
    body.append("    </nav>\n")
    body.append("  </article>\n</main>\n")

    body.append(FOOT.format(home="../index.html", repo=p["repo"], js="../app.js"))

    # structured data
    ld = {
        "@context": "https://schema.org",
        "@type": "SoftwareSourceCode",
        "name": p["name"],
        "description": desc,
        "codeRepository": p["repo"],
        "programmingLanguage": p["lang"],
        "license": "https://www.gnu.org/licenses/agpl-3.0.html" if p["license"] == "AGPL-3.0" else "https://opensource.org/licenses/MIT",
        "url": f"https://codevortax.github.io/projects/{slug}.html",
    }
    out = "".join(body).replace(
        "</head>",
        f'<script type="application/ld+json">{json.dumps(ld)}</script>\n</head>',
    )
    return out


def landing_page(projects):
    """The landing page: hero, filterable card grid, about."""
    total_stars = sum(p["stars"] for p in projects)
    agpl = sum(1 for p in projects if p["license"] == "AGPL-3.0")
    langs = len({p["lang"].split(" / ")[0] for p in projects})

    cards = []
    for p in projects:
        featured = " featured" if p["slug"] == "focus" else ""
        cards.append(
            f'      <a class="card{featured} reveal" href="projects/{p["slug"]}.html" data-cat="{p["cat"]}">\n'
            '        <div class="card-top">\n'
            f'          <h3>{p["name"]}</h3>\n'
            f'          <span class="badge">★ {p["stars"]}</span>\n'
            "        </div>\n"
            f'        <p>{CARD_BLURBS.get(p["slug"], re.sub("<[^>]+>", "", p["tagline"]))}</p>\n'
            '        <div class="meta">\n'
            f'          <span class="lang"><i style="--c:{p["color"]}"></i>{p["lang"]}</span>\n'
            f'          <span>{p["license"]}</span>\n'
            '          <span class="go" aria-hidden="true">Read more →</span>\n'
            "        </div>\n"
            "      </a>\n"
        )

    extra = f'<script type="application/ld+json">{json.dumps(JSON_LD_EXTRA)}</script>\n'

    page = HEAD.format(
        title="CodeVortax — Android apps, ESP32 firmware and CLI tools",
        desc="Open source Android apps, ESP32 firmware and command-line tools. Local-first, offline by default, no accounts and no tracking.",
        path="",
        css="style.css",
        extra=extra,
    )
    page += NAV.format(home="index.html")
    page += """
<main id="top">

  <section class="hero">
    <div class="blob b1" aria-hidden="true"></div>
    <div class="blob b2" aria-hidden="true"></div>
    <div class="grid-bg" aria-hidden="true"></div>
    <div class="hero-inner">
      <p class="eyebrow"><span class="dot" aria-hidden="true"></span>Open source · Android · ESP32 · Python</p>
      <h1>CodeVortax</h1>
      <p class="lead">Android apps, ESP32 firmware and small sharp command-line tools. Local-first, offline by default, no accounts and no tracking. Every project has its own page here, not just a link to GitHub.</p>
      <div class="cta">
        <a class="btn primary" href="#projects">See the projects</a>
        <a class="btn ghost" href="https://github.com/CodeVortax">GitHub profile</a>
      </div>
      <ul class="stats">
"""
    page += f'        <li><b>{len(projects)}</b><span>projects</span></li>\n'
    page += f'        <li><b>{langs}</b><span>languages</span></li>\n'
    page += f'        <li><b>{total_stars}</b><span>stars</span></li>\n'
    page += f'        <li><b>{agpl}</b><span>AGPL-3.0</span></li>\n'
    page += """      </ul>
    </div>
  </section>

  <section id="projects" class="section">
    <div class="section-head reveal">
      <h2>Projects</h2>
      <p>Thirteen projects, each with its own page: what it does, how it works, how to install it and what to watch out for. Source is on GitHub.</p>
    </div>

    <div class="chips reveal" role="group" aria-label="Filter projects by category">
      <button class="chip is-active" data-filter="all" aria-pressed="true">All</button>
      <button class="chip" data-filter="android" aria-pressed="false">Android</button>
      <button class="chip" data-filter="esp32" aria-pressed="false">ESP32</button>
      <button class="chip" data-filter="tool" aria-pressed="false">CLI &amp; tools</button>
      <button class="chip" data-filter="web" aria-pressed="false">Web</button>
    </div>

    <p class="empty" id="empty" hidden>No projects in this category.</p>

    <div class="grid" id="grid">
"""
    page += "".join(cards)
    page += """    </div>

    <p class="more reveal">
      <a href="projects.html">Browse every project as a list <span aria-hidden="true">→</span></a>
    </p>
  </section>

  <section id="about" class="section">
    <div class="section-head reveal">
      <h2>About</h2>
      <p>Small tools that do one thing well, and keep your data on your own device.</p>
    </div>

    <div class="cols">
      <article class="col reveal from-left">
        <h3>Android apps</h3>
        <p>Kotlin apps built around privacy: no accounts, no analytics, no internet permission where it isn't needed. <em>focus</em>, <em>Crystal</em> and <em>swipe-tally</em> all run fully offline.</p>
      </article>
      <article class="col reveal">
        <h3>ESP32 firmware</h3>
        <p>Boards that serve their own web app over WiFi &mdash; an IR test bench, and a repeater that meters and limits each device &mdash; so the phone in your hand is the control panel.</p>
      </article>
      <article class="col reveal from-right">
        <h3>Termux tooling</h3>
        <p>Most of the Python here is made to work from a phone: bridging USB to <code>esptool</code>, reading right-to-left text, QEMU, and downloads that survive a dropped connection.</p>
      </article>
    </div>
  </section>

</main>
"""
    page += FOOT.format(home="index.html", repo="https://github.com/CodeVortax", js="app.js")
    return page


def index_page(projects):
    """A plain list of every project page, for no-JS and for crawlers."""
    rows = []
    for p in projects:
        desc = re.sub("<[^>]+>", "", p["tagline"])
        rows.append(
            f'      <li class="row reveal">\n'
            f'        <a href="projects/{p["slug"]}.html">\n'
            f'          <span class="row-name">{p["name"]}</span>\n'
            f'          <span class="row-desc">{desc}</span>\n'
            f'          <span class="row-meta">{p["lang"]} · {p["license"]}</span>\n'
            "        </a>\n"
            "      </li>\n"
        )

    page = HEAD.format(
        title="All projects — CodeVortax",
        desc="Every CodeVortax project, with a page of its own: Android apps, ESP32 firmware, CLI and web tools.",
        path="projects.html",
        css="style.css",
        extra="",
    )
    page += NAV.format(home="index.html")
    page += """
<main id="main">
  <section class="section">
    <div class="section-head reveal">
      <h2>All projects</h2>
      <p>Thirteen pages, one per project. Each one covers what it does, how to install it, how to use it and what to watch out for.</p>
    </div>
    <ul class="rows">
"""
    page += "".join(rows)
    page += """    </ul>
    <p class="more reveal"><a href="index.html#projects">Back to the overview <span aria-hidden="true">→</span></a></p>
  </section>
</main>
"""
    page += FOOT.format(home="index.html", repo="https://github.com/CodeVortax", js="app.js")
    return page


def main():
    projects = load()
    OUT.mkdir(exist_ok=True)

    for i, p in enumerate(projects):
        prev_p = projects[i - 1] if i > 0 else None
        next_p = projects[i + 1] if i + 1 < len(projects) else None
        target = OUT / f'{p["slug"]}.html'
        target.write_text(project_page(p, prev_p, next_p), encoding="utf-8")

    (ROOT / "index.html").write_text(landing_page(projects), encoding="utf-8")
    (ROOT / "projects.html").write_text(index_page(projects), encoding="utf-8")
    print(f"wrote {len(projects)} project pages, index.html, projects.html")


if __name__ == "__main__":
    main()
