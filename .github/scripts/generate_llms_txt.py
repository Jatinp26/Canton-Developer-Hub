#!/usr/bin/env python3

import html
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

SOURCE = Path("Github Page") / "tools.json"
DEST_TXT = Path("Github Page") / "llms.txt"
DEST_HTML = Path("Github Page") / "catalog.html"

def load_by_category(tools):
    by_category = defaultdict(list)
    for t in tools:
        by_category[t.get("category", "Other")].append(t)
    return by_category

def generate_txt(tools, by_category):
    lines = [
        "# Canton Developer Hub — Ecosystem Tool Catalog",
        "",
        "> Canton Developer Hub (dev-hub.canton.foundation) is the community Maintained catalog of ecosystem tooling for building on Canton Network. This is a plain-text index for AI assistants; the interactive version with filtering is at https://dev-hub.canton.foundation.",
        "",
    ]
    for category in sorted(by_category):
        lines.append(f"## {category}")
        lines.append("")
        for t in sorted(by_category[category], key=lambda x: x["name"]):
            name = t["name"]
            maker = t.get("maker", "Unknown")
            desc = t.get("desc", "")
            dev_fund = " (Canton Foundation Dev Fund)" if t.get("dev_fund") else ""
            ttype = t.get("type", "")
            primary_link = t["links"][0]["url"] if t.get("links") else ""
            updated = t.get("last_updated", "")
            lines.append(
                f"- [{name}]({primary_link}): {desc} — Maker: {maker}{dev_fund}. "
                f"Type: {ttype}. Last updated: {updated}."
            )
        lines.append("")
    lines.append("---")
    lines.append("Generated automatically from tools.json. Do not edit by hand.")
    lines.append(f"Generated: {date.today().isoformat()}")
    return "\n".join(lines)


def shared_style_block():
    return """
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&display=swap" rel="stylesheet" />
<style>
  :root {
    --yellow: #F3FF97; --black: #030206; --white: #FFFFFC;
    --lilac: #D5A5E3; --purple: #875CFF; --taupe: #A89F91;
    --bg: #FFFFFC; --surface: #f4f3f0;
    --border: rgba(3,2,6,0.18); --border-md: rgba(3,2,6,0.22);
    --text: #030206; --muted: #5a5860; --hint: #9a97a0;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'IBM Plex Sans', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; -webkit-font-smoothing: antialiased; }
  a { color: var(--purple); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .site-header { background: var(--black); padding: 0 2rem; display: flex; align-items: center; justify-content: space-between; height: 56px; }
  .logo { font-size: 16px; font-weight: 500; color: var(--white); }
  .header-btn { font-family: inherit; font-size: 13px; font-weight: 400; padding: 6px 14px; border-radius: 100px; border: 1px solid rgba(255,255,252,0.2); color: var(--white); }
  .header-btn:hover { border-color: rgba(255,255,252,0.5); text-decoration: none; }
  .hero { background: var(--black); padding: 2.5rem 2rem 2rem; }
  .hero-inner { max-width: 960px; margin: 0 auto; }
  .hero-eyebrow { font-size: 12px; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; color: var(--taupe); margin-bottom: 0.5rem; }
  .hero h1 { font-size: clamp(24px, 4vw, 36px); font-weight: 300; color: var(--white); line-height: 1.2; margin-bottom: 0.5rem; }
  .hero p { font-size: 15px; font-weight: 300; color: var(--taupe); max-width: 600px; line-height: 1.6; }
  .hero p a { color: var(--yellow); }
  .main { max-width: 960px; margin: 0 auto; padding: 2rem 1rem 4rem; }
  .catnav { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 1.5rem; }
  .catnav a { font-size: 13px; font-weight: 500; padding: 5px 13px; border-radius: 100px; border: 1.5px solid var(--border); color: var(--muted); }
  .catnav a.current { background: var(--black); color: var(--lilac); border-color: var(--black); font-weight: 600; }
  .catnav a:hover { border-color: var(--border-md); color: var(--text); text-decoration: none; }
  h2.section { font-size: 13px; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase; color: var(--muted); margin: 2rem 0 0.9rem; padding-top: 1rem; border-top: 1px solid var(--border); }
  h2.section:first-of-type { border-top: none; padding-top: 0; margin-top: 0; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
  .card { background: var(--bg); border: 1px solid var(--border); border-radius: 14px; padding: 1.4rem; display: flex; flex-direction: column; gap: 8px; }
  .card-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
  .card-name { font-size: 15px; font-weight: 500; color: var(--text); }
  .card-name a { color: var(--text); }
  .card-maker { font-size: 12.5px; color: var(--hint); font-weight: 600; margin-top: 2px; }
  .badge { font-size: 12px; font-weight: 600; padding: 3px 9px; border-radius: 100px; white-space: nowrap; flex-shrink: 0; }
  .badge.official { background: var(--yellow); color: var(--black); }
  .badge.partner { background: rgba(213,165,227,0.25); color: #4a2060; }
  .badge-devfund { display: inline-block; font-size: 11.5px; font-weight: 600; padding: 2px 9px; border-radius: 100px; background: rgba(76,175,80,0.12); color: #2e7d32; border: 1px solid rgba(76,175,80,0.35); }
  .card-desc { font-size: 13px; color: var(--muted); line-height: 1.6; }
  .card-meta { font-size: 11.5px; color: #313130; margin-top: 2px; }
  .site-footer { background: var(--black); padding: 1.75rem; text-align: center; font-size: 13px; color: var(--taupe); font-weight: 300; }
  .site-footer a { color: var(--yellow); }
</style>"""


def render_tool_card(t):
    dev_fund = ' <span class="badge-devfund">Dev Fund</span>' if t.get("dev_fund") else ""
    ttype = t.get("type", "partner")
    badge_label = "Official" if ttype == "official" else "Partner tooling"
    link = html.escape(t["links"][0]["url"]) if t.get("links") else "#"
    updated = html.escape(t.get("last_updated", ""))
    return f"""    <div class="card">
      <div class="card-top">
        <div>
          <div class="card-name"><a href="{link}">{html.escape(t['name'])}</a></div>
          <div class="card-maker">{html.escape(t.get('maker', 'Unknown'))}</div>
        </div>
        <span class="badge {html.escape(ttype)}">{badge_label}</span>
      </div>
      <div>{dev_fund}</div>
      <div class="card-desc">{html.escape(t.get('desc', ''))}</div>
      <div class="card-meta">Last updated: {updated}</div>
    </div>

def generate_html(tools, by_category):
    page_url = "https://canton-network-devs.github.io/Canton-Developer-Hub/catalog.html"
    site_url = "https://canton-network-devs.github.io/Canton-Developer-Hub/"

    list_items = []
    for i, t in enumerate(tools, start=1):
        entry = {
            "@type": "ListItem", "position": i,
            "item": {
                "@type": "SoftwareApplication", "name": t["name"],
                "description": t.get("desc", ""), "applicationCategory": t.get("category", ""),
                "creator": {"@type": "Organization", "name": t.get("maker", "Unknown")},
                "url": t["links"][0]["url"] if t.get("links") else None,
                "dateModified": t.get("last_updated", ""),
            },
        }
        if t.get("dev_fund"):
            entry["item"]["funder"] = {"@type": "Organization", "name": "Canton Foundation Dev Fund"}
        list_items.append(entry)

    json_ld = json.dumps({
        "@context": "https://schema.org", "@type": "ItemList",
        "name": "Canton Developer Hub — Ecosystem Tool Catalog",
        "description": ("Community-maintained catalog of ecosystem tooling for building "
                         "on Canton Network, including official Canton Network SDKs/APIs, "
                         "Canton Foundation Dev Fund-funded projects, and community-built tools."),
        "numberOfItems": len(tools), "itemListElement": list_items,
    })

    parts = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Canton Developer Hub — Ecosystem Tool Catalog</title>",
        '<meta name="description" content="Static, crawlable index of Canton '
        'Network ecosystem tools, SDKs, and APIs for AI assistants and search engines.">',
        f'<link rel="canonical" href="{page_url}">',
        '<meta property="og:type" content="website">',
        '<meta property="og:title" content="Canton Developer Hub — Ecosystem Tool Catalog">',
        '<meta property="og:description" content="Community-maintained catalog of '
        'ecosystem tooling for building on Canton Network.">',
        f'<meta property="og:url" content="{page_url}">',
        '<meta property="og:site_name" content="Canton Developer Hub">',
        '<script type="application/ld+json">' + json_ld + "</script>",
        shared_style_block(),
        "</head><body>",
        '<header class="site-header"><div class="logo">Build on Canton</div>'
        f'<a class="header-btn" href="{site_url}">Interactive version →</a></header>',
        '<section class="hero"><div class="hero-inner">',
        '<p class="hero-eyebrow">All Open-Source</p>',
        "<h1>Ecosystem Tool Catalog</h1>",
        "<p>Official Canton Network SDKs/APIs, Canton Foundation Dev Fund-funded "
        "projects, and other community-built tools — all in one place. "
        f'For filtering, search, and reactions, use the <a href="{site_url}">interactive Dev Hub</a>.</p>',
        "</div></section>",
        '<main class="main">',
    ]

    for category in sorted(by_category):
        parts.append(f'<h2 class="section">{html.escape(category)}</h2>')
        parts.append('<div class="grid">')
        for t in sorted(by_category[category], key=lambda x: x["name"]):
            parts.append(render_tool_card(t))
        parts.append("</div>")

    parts.append("</main>")
    parts.append(
        f'<footer class="site-footer">Generated automatically from tools.json on '
        f'{date.today().isoformat()}. Maintained by <a href="https://canton.foundation/" '
        'target="_blank">Canton Foundation</a>.</footer>'
    )
    parts.append("</body></html>")
    return "\n".join(parts)

def slugify(category):
    return re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-")

def generate_category_html(category, tools_in_cat, all_categories):
    """A focused, single-category page — smaller and more retrievable than
    one page listing all 47 tools (per Mintlify support: 'only a portion of
    a page comes back with each search result, so one large page works
    against retrieval')."""
    page_url = f"https://canton-network-devs.github.io/Canton-Developer-Hub/catalog/{slugify(category)}.html"
    site_url = "https://canton-network-devs.github.io/Canton-Developer-Hub/"

    list_items = []
    for i, t in enumerate(tools_in_cat, start=1):
        entry = {
            "@type": "ListItem", "position": i,
            "item": {
                "@type": "SoftwareApplication", "name": t["name"],
                "description": t.get("desc", ""), "applicationCategory": t.get("category", ""),
                "creator": {"@type": "Organization", "name": t.get("maker", "Unknown")},
                "url": t["links"][0]["url"] if t.get("links") else None,
                "dateModified": t.get("last_updated", ""),
            },
        }
        if t.get("dev_fund"):
            entry["item"]["funder"] = {"@type": "Organization", "name": "Canton Foundation Dev Fund"}
        list_items.append(entry)

    json_ld = json.dumps({
        "@context": "https://schema.org", "@type": "ItemList",
        "name": f"Canton Developer Hub — {category}",
        "description": f"Canton Network ecosystem tools in the {category} category.",
        "numberOfItems": len(tools_in_cat), "itemListElement": list_items,
    })

    catnav = "".join(
        f'<a href="{slugify(c)}.html" class="{"current" if c == category else ""}">{html.escape(c)}</a>'
        for c in sorted(all_categories)
    )

    parts = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>Canton Developer Hub — {html.escape(category)} Tools</title>",
        f'<meta name="description" content="Canton Network {html.escape(category)} '
        'tools, SDKs, and integrations for building on Canton.">',
        f'<link rel="canonical" href="{page_url}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:title" content="Canton Developer Hub — {html.escape(category)} Tools">',
        f'<meta property="og:url" content="{page_url}">',
        '<meta property="og:site_name" content="Canton Developer Hub">',
        '<script type="application/ld+json">' + json_ld + "</script>",
        shared_style_block(),
        "</head><body>",
        '<header class="site-header"><div class="logo">Build on Canton</div>'
        f'<a class="header-btn" href="{site_url}">Interactive version →</a></header>',
        '<section class="hero"><div class="hero-inner">',
        '<p class="hero-eyebrow">All Open-Source</p>',
        f"<h1>{html.escape(category)}</h1>",
        f'<p><a href="../catalog.html">← Full catalog</a> · For filtering and search, '
        f'use the <a href="{site_url}">interactive Dev Hub</a>.</p>',
        "</div></section>",
        '<main class="main">',
        f'<nav class="catnav">{catnav}</nav>',
        '<div class="grid">',
    ]
    for t in sorted(tools_in_cat, key=lambda x: x["name"]):
        parts.append(render_tool_card(t))
    parts.append("</div></main>")
    parts.append(
        f'<footer class="site-footer">Generated automatically from tools.json on '
        f'{date.today().isoformat()}. Maintained by <a href="https://canton.foundation/" '
        'target="_blank">Canton Foundation</a>.</footer>'
    )
    parts.append("</body></html>")
    return "\n".join(parts)

def generate_sitemap(by_category, tools):
    today = date.today().isoformat()
    urls = [
        ("https://canton-network-devs.github.io/Canton-Developer-Hub/", "1.0"),
        ("https://canton-network-devs.github.io/Canton-Developer-Hub/catalog.html", "0.9"),
    ]
    for category in sorted(by_category):
        urls.append((
            f"https://canton-network-devs.github.io/Canton-Developer-Hub/catalog/{slugify(category)}.html",
            "0.8",
        ))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, priority in urls:
        lines.append(f"  <url><loc>{url}</loc><lastmod>{today}</lastmod><priority>{priority}</priority></url>")
    lines.append("</urlset>")
    return "\n".join(lines)

def main():
    tools = json.loads(SOURCE.read_text())
    by_category = load_by_category(tools)

    DEST_TXT.write_text(generate_txt(tools, by_category))
    DEST_HTML.write_text(generate_html(tools, by_category))

    catalog_dir = Path("Github Page") / "catalog"
    catalog_dir.mkdir(exist_ok=True)
    all_categories = list(by_category.keys())
    for category, tools_in_cat in by_category.items():
        page = generate_category_html(category, tools_in_cat, all_categories)
        (catalog_dir / f"{slugify(category)}.html").write_text(page)

    (Path("Github Page") / "sitemap.xml").write_text(generate_sitemap(by_category, tools))
    
    print(
        f"Wrote {DEST_TXT}, {DEST_HTML}, {len(by_category)} category pages under "
        f"{catalog_dir}/, sitemap.xml, and robots.txt — {len(tools)} tools across "
        f"{len(by_category)} categories"
    )

if __name__ == "__main__":
    main()
