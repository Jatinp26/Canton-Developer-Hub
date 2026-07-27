#!/usr/bin/env python3
"""
Generates two static, JavaScript-free outputs from Dev Hub's tools.json:

  1. llms.txt      — the llms.txt-standard plain-text catalog, for AI tools
                      that fetch it directly (e.g. pasted into a chat, or
                      an LLM given the URL as context).
  2. catalog.html   — a genuine server-rendered HTML page with the same
                      content, for crawlers (like Mintlify's Search Domains
                      feature) that only index real HTML pages and won't
                      treat a bare .txt file as a knowledge source.

Run from the REPO ROOT (GitHub Actions does this by default via
actions/checkout):

    python3 .github/scripts/generate_llms_txt.py

Reads:  Github Page/tools.json
Writes: Github Page/llms.txt
        Github Page/catalog.html
"""
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
        "> Canton Developer Hub (dev-hub.canton.foundation) is the community-maintained catalog of ecosystem tooling for building on Canton Network. This is a plain-text index for AI assistants; the interactive version with filtering is at https://dev-hub.canton.foundation.",
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

def generate_html(tools, by_category):
    page_url = "https://canton-network-devs.github.io/Canton-Developer-Hub/catalog.html"
    site_url = "https://canton-network-devs.github.io/Canton-Developer-Hub/"

    list_items = []
    for i, t in enumerate(tools, start=1):
        entry = {
            "@type": "ListItem",
            "position": i,
            "item": {
                "@type": "SoftwareApplication",
                "name": t["name"],
                "description": t.get("desc", ""),
                "applicationCategory": t.get("category", ""),
                "creator": {"@type": "Organization", "name": t.get("maker", "Unknown")},
                "url": t["links"][0]["url"] if t.get("links") else None,
                "dateModified": t.get("last_updated", ""),
            },
        }
        if t.get("dev_fund"):
            entry["item"]["funder"] = {
                "@type": "Organization",
                "name": "Canton Foundation Dev Fund",
            }
        list_items.append(entry)

    json_ld = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": "Canton Developer Hub — Ecosystem Tool Catalog",
            "description": (
                "Community-maintained catalog of ecosystem tooling for building "
                "on Canton Network, including official Canton Network SDKs/APIs, "
                "Canton Foundation Dev Fund-funded projects, and community-built tools."
            ),
            "numberOfItems": len(tools),
            "itemListElement": list_items,
        },
        indent=None,
    )

    parts = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Canton Developer Hub — Ecosystem Tool Catalog</title>",
        '<meta name="description" content="Static, crawlable index of Canton '
        'Network ecosystem tools, SDKs, and APIs for AI assistants and search engines.">',
        f'<link rel="canonical" href="{page_url}">',
        # Open Graph tags — help search engines and AI crawlers understand
        # page identity and purpose at a glance.
        '<meta property="og:type" content="website">',
        '<meta property="og:title" content="Canton Developer Hub — Ecosystem Tool Catalog">',
        '<meta property="og:description" content="Community-maintained catalog of '
        'ecosystem tooling for building on Canton Network.">',
        f'<meta property="og:url" content="{page_url}">',
        f'<meta property="og:site_name" content="Canton Developer Hub">',
        # JSON-LD structured data — machine-readable description of every
        # tool listed, using schema.org SoftwareApplication.
        '<script type="application/ld+json">' + json_ld + "</script>",
        "</head><body>",
        "<h1>Canton Developer Hub — Ecosystem Tool Catalog</h1>",
        "<p>Canton Developer Hub is the community-maintained catalog of ecosystem "
        "tooling for building on Canton Network — official Canton Network SDKs/APIs, "
        "Canton Foundation Dev Fund-funded projects, and other community-built tools. "
        f'The interactive version is at <a href="{site_url}">the Canton Developer Hub</a>.</p>',
    ]
    for category in sorted(by_category):
        parts.append(f"<h2>{html.escape(category)}</h2>")
        parts.append("<ul>")
        for t in sorted(by_category[category], key=lambda x: x["name"]):
            name = html.escape(t["name"])
            maker = html.escape(t.get("maker", "Unknown"))
            desc = html.escape(t.get("desc", ""))
            dev_fund = " (Canton Foundation Dev Fund)" if t.get("dev_fund") else ""
            ttype = html.escape(t.get("type", ""))
            link = html.escape(t["links"][0]["url"]) if t.get("links") else "#"
            updated = html.escape(t.get("last_updated", ""))
            parts.append(
                f'<li><a href="{link}">{name}</a>: {desc} — Maker: {maker}{dev_fund}. '
                f"Type: {ttype}. Last updated: {updated}.</li>"
            )
        parts.append("</ul>")
    parts.append(
        f"<hr><p><em>Generated automatically from tools.json on {date.today().isoformat()}. "
        "Do not edit by hand.</em></p>"
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

    list_items = []
    for i, t in enumerate(tools_in_cat, start=1):
        entry = {
            "@type": "ListItem",
            "position": i,
            "item": {
                "@type": "SoftwareApplication",
                "name": t["name"],
                "description": t.get("desc", ""),
                "applicationCategory": t.get("category", ""),
                "creator": {"@type": "Organization", "name": t.get("maker", "Unknown")},
                "url": t["links"][0]["url"] if t.get("links") else None,
                "dateModified": t.get("last_updated", ""),
            },
        }
        if t.get("dev_fund"):
            entry["item"]["funder"] = {"@type": "Organization", "name": "Canton Foundation Dev Fund"}
        list_items.append(entry)

    json_ld = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": f"Canton Developer Hub — {category}",
            "description": f"Canton Network ecosystem tools in the {category} category.",
            "numberOfItems": len(tools_in_cat),
            "itemListElement": list_items,
        }
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
        "</head><body>",
        f"<h1>Canton Developer Hub — {html.escape(category)}</h1>",
        '<p><a href="../catalog.html">← Full catalog</a> | '
        + " | ".join(
            f'<a href="{slugify(c)}.html">{html.escape(c)}</a>' if c != category else html.escape(c)
            for c in sorted(all_categories)
        )
        + "</p>",
        "<ul>",
    ]
    for t in sorted(tools_in_cat, key=lambda x: x["name"]):
        name = html.escape(t["name"])
        maker = html.escape(t.get("maker", "Unknown"))
        desc = html.escape(t.get("desc", ""))
        dev_fund = " (Canton Foundation Dev Fund)" if t.get("dev_fund") else ""
        ttype = html.escape(t.get("type", ""))
        link = html.escape(t["links"][0]["url"]) if t.get("links") else "#"
        updated = html.escape(t.get("last_updated", ""))
        parts.append(
            f'<li><a href="{link}">{name}</a>: {desc} — Maker: {maker}{dev_fund}. '
            f"Type: {ttype}. Last updated: {updated}.</li>"
        )
    parts.append("</ul></body></html>")
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

def generate_robots_txt():
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Sitemap: https://canton-network-devs.github.io/Canton-Developer-Hub/sitemap.xml\n"
    )

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
    (Path("Github Page") / "robots.txt").write_text(generate_robots_txt())

    print(
        f"Wrote {DEST_TXT}, {DEST_HTML}, {len(by_category)} category pages under "
        f"{catalog_dir}/, sitemap.xml, and robots.txt — {len(tools)} tools across "
        f"{len(by_category)} categories"
    )

if __name__ == "__main__":
    main()
