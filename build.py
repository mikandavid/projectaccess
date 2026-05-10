"""Compile bilingual Project Access Austria pages from JSON content + Jinja2 templates.

Usage:
    python build.py [--clean]

Reads:
    content/_site.json          shared chrome (nav, footer, press)
    content/<page>.json         bilingual content for each page
    templates/<page>.html.j2    Jinja2 template per page

Writes:
    German pages at the repository root, English pages under en/.
    The set of pages and their per-language slugs is defined in PAGES below.
    Also writes sitemap.xml, robots.txt and llms.txt for SEO/AI discovery.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
    from markupsafe import Markup, escape
except ImportError as exc:  # pragma: no cover
    sys.stderr.write(
        "Jinja2 is required. Install it with:\n"
        "    python -m pip install -r requirements.txt\n"
    )
    raise SystemExit(1) from exc

ROOT = Path(__file__).resolve().parent
CONTENT_DIR = ROOT / "content"
TEMPLATES_DIR = ROOT / "templates"

LANGUAGES: list[str] = ["de", "en"]

# Public site origin used for canonical, hreflang, sitemap and Open Graph URLs.
# Read once from content/_site.json so the value lives next to the rest of the
# bilingual site chrome.
SITE_URL = "https://projectaccess.at"

# Per-page sitemap weighting. Higher priority pages get crawled/refreshed more
# eagerly. Values stay between 0.0 and 1.0; the home page outranks the rest.
SITEMAP_PRIORITY: dict[str, float] = {
    "index":    1.0,
    "bootcamp": 0.9,
    "events":   0.7,
    "team":     0.7,
    "partners": 0.6,
}

SITEMAP_CHANGEFREQ: dict[str, str] = {
    "index":    "weekly",
    "bootcamp": "weekly",
    "events":   "monthly",
    "team":     "monthly",
    "partners": "monthly",
}

# Maps logical page key -> per-language output path relative to ROOT.
# German pages live at the root, English pages under en/ with English slugs.
PAGES: dict[str, dict[str, str]] = {
    "index":    {"de": "index.html",    "en": "en/index.html"},
    "bootcamp": {"de": "bootcamp.html", "en": "en/bootcamp.html"},
    "events":   {"de": "events.html",   "en": "en/events.html"},
    "partners": {"de": "partners.html", "en": "en/partners.html"},
    "team":     {"de": "team.html",     "en": "en/team.html"},
}

# Localised section anchors. Use anchor("programme") in templates to render the
# right id/href fragment for the current language.
ANCHORS: dict[str, dict[str, str]] = {
    "programme":  {"de": "programm",   "en": "programme"},
    "bootcamp":   {"de": "bootcamp",   "en": "bootcamp"},
    "engagement": {"de": "engagement", "en": "engagement"},
    "team":       {"de": "team",       "en": "team"},
    "contact":    {"de": "kontakt",    "en": "contact"},
    "schools":    {"de": "schulen",    "en": "schools"},
}

# Each output file ends up either at the root (depth 0) or under en/ (depth 1).
# We need a relative path from there back to the repo root for shared assets.
_MARK_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)


def mark_filter(value: str) -> Markup:
    """Render `**word**` as `<span class="mark">word</span>`, escaping the rest."""
    if value is None:
        return Markup("")
    text = str(value)
    parts: list[str] = []
    last = 0
    for match in _MARK_RE.finditer(text):
        parts.append(str(escape(text[last : match.start()])))
        parts.append(f'<span class="mark">{escape(match.group(1))}</span>')
        last = match.end()
    parts.append(str(escape(text[last:])))
    return Markup("".join(parts))


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def relative_url(target_path: str, current_dir: str) -> str:
    """Compute a relative URL from current_dir (e.g. "" or "en/") to target_path
    (a repo-root-relative path like "en/bootcamp.html")."""
    if not current_dir:
        return target_path
    if target_path.startswith(current_dir):
        return target_path[len(current_dir):]
    # Currently the only nested directory is en/, so a single "../" is enough.
    return "../" + target_path


def public_url(rel_path: str) -> str:
    """Convert a repo-root-relative output path to its public absolute URL.

    The home pages map to clean directory URLs ("/" and "/en/") so search
    engines and social platforms see a single canonical form. Every other page
    keeps its filename so existing inbound links keep working.
    """
    if rel_path == "index.html":
        return f"{SITE_URL}/"
    if rel_path == "en/index.html":
        return f"{SITE_URL}/en/"
    return f"{SITE_URL}/{rel_path}"


def absolute_asset_url(rel_path: str) -> str:
    """Public URL for an asset path (e.g. assets/foo.jpg) that lives at root."""
    if rel_path.startswith(("http://", "https://")):
        return rel_path
    return f"{SITE_URL}/{rel_path.lstrip('/')}"


def build_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )
    env.filters["mark"] = mark_filter
    return env


def compute_asset_prefix(current_dir: str) -> str:
    return "" if not current_dir else "../"


def render_page(
    env: Environment,
    page_key: str,
    lang: str,
    site: dict,
    page_content: dict,
) -> str:
    output_rel = PAGES[page_key][lang]
    current_dir = "en/" if lang == "en" else ""

    other_lang = "en" if lang == "de" else "de"
    self_href = relative_url(output_rel, current_dir)
    alt_lang_href = relative_url(PAGES[page_key][other_lang], current_dir)

    canonical_url = public_url(output_rel)
    canonical_url_alt = public_url(PAGES[page_key][other_lang])
    canonical_de = canonical_url if lang == "de" else canonical_url_alt
    canonical_en = canonical_url if lang == "en" else canonical_url_alt

    # Open Graph / Twitter card image. Pages can override via meta.og_image.
    og_image_meta = page_content.get("meta", {}).get("og_image") or site["default_og_image"]
    og_image_url = absolute_asset_url(og_image_meta["src"])
    og_image_alt = og_image_meta.get("alt", {}).get(lang) if isinstance(og_image_meta.get("alt"), dict) else og_image_meta.get("alt")

    asset_prefix = compute_asset_prefix(current_dir)

    def asset(rel: str) -> str:
        return f"{asset_prefix}{rel}"

    def anchor(key: str) -> str:
        return ANCHORS[key][lang]

    def t(value):
        """Resolve a {de, en} dict to the current language; pass strings through."""
        if isinstance(value, dict) and "de" in value and "en" in value:
            return value[lang]
        return value

    def page_href(target_page: str, anchor_key: str | None = None) -> str:
        target = PAGES[target_page][lang]
        url = relative_url(target, current_dir)
        if anchor_key:
            url = f"{url}#{ANCHORS[anchor_key][lang]}"
        return url

    context: dict = {
        "lang": lang,
        "page_key": page_key,
        "page": page_content,
        "site": site,
        "self_href": self_href,
        "alt_lang_href": alt_lang_href,
        "asset_prefix": asset_prefix,
        "asset": asset,
        "anchor": anchor,
        "page_href": page_href,
        "t": t,
        "canonical_url": canonical_url,
        "canonical_de": canonical_de,
        "canonical_en": canonical_en,
        "og_image_url": og_image_url,
        "og_image_alt": og_image_alt,
        "absolute_asset_url": absolute_asset_url,
        "site_url": SITE_URL,
    }

    if page_key == "index":
        team_data = load_json(CONTENT_DIR / "team.json")
        members_by_key = {m["key"]: m for m in team_data["members"]}
        preview_keys = page_content["team_preview"]["members_keys"]
        context["team_preview_members"] = [members_by_key[k] for k in preview_keys]
    elif page_key == "team":
        members_by_key = {m["key"]: m for m in page_content["members"]}
        context["team_members"] = page_content["members"]
        context["team_groups"] = [
            {
                "title": group["title"],
                "members": [members_by_key[k] for k in group["member_keys"]],
            }
            for group in page_content.get("groups", [])
        ]

    template = env.get_template(f"{page_key}.html.j2")
    return template.render(**context)


def write_file(rel_path: str, content: str) -> None:
    out = ROOT / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(f"  wrote {rel_path}")


SEO_OUTPUTS = ("sitemap.xml", "robots.txt", "llms.txt")


def clean_outputs() -> None:
    for variants in PAGES.values():
        for rel in variants.values():
            target = ROOT / rel
            if target.exists():
                target.unlink()
    for name in SEO_OUTPUTS:
        target = ROOT / name
        if target.exists():
            target.unlink()
    en_dir = ROOT / "en"
    if en_dir.exists() and not any(en_dir.iterdir()):
        shutil.rmtree(en_dir)


def render_sitemap() -> str:
    """Generate an XML sitemap with hreflang alternates for every page."""
    today = date.today().isoformat()
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    for page_key, variants in PAGES.items():
        priority = SITEMAP_PRIORITY.get(page_key, 0.5)
        changefreq = SITEMAP_CHANGEFREQ.get(page_key, "monthly")
        for lang in LANGUAGES:
            loc = public_url(variants[lang])
            lines.append("  <url>")
            lines.append(f"    <loc>{loc}</loc>")
            lines.append(f"    <lastmod>{today}</lastmod>")
            lines.append(f"    <changefreq>{changefreq}</changefreq>")
            lines.append(f"    <priority>{priority:.1f}</priority>")
            for alt_lang in LANGUAGES:
                alt_loc = public_url(variants[alt_lang])
                lines.append(
                    f'    <xhtml:link rel="alternate" hreflang="{alt_lang}" href="{alt_loc}" />'
                )
            lines.append(
                f'    <xhtml:link rel="alternate" hreflang="x-default" href="{public_url(variants["en"])}" />'
            )
            lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")
    return "\n".join(lines)


def render_robots() -> str:
    """robots.txt: allow everything, point at the sitemap, block known noisy paths."""
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /mitmachen.html\n"
        "Disallow: /en/get-involved.html\n"
        "\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
    )


def render_llms_txt(site: dict) -> str:
    """Curated map of priority pages for AI assistants that honour llms.txt."""
    org = site["organization"]
    description = org["description"]["en"]
    sections = [
        f"# {site['site_name']}",
        "",
        f"> {description}",
        "",
        "Project\u00a0Access\u00a0Austria (legal name: Projekt Hochschulzugang) is the Austrian "
        "chapter of the international Project\u00a0Access network. We help students from "
        "Austria and South Tyrol apply to selective international universities such as "
        "Oxford, Cambridge, Harvard, ETH Zürich and Sciences Po. All support is free.",
        "",
        "## Core pages",
        "",
        f"- [Home (Deutsch)]({public_url('index.html')}): mission, programme overview, bootcamp summary, team, contact.",
        f"- [Home (English)]({public_url('en/index.html')}): mission, programme overview, bootcamp summary, team, contact.",
        f"- [Bootcamp 2026 (Deutsch)]({public_url('bootcamp.html')}): dates (23–26\u00a0July\u00a02026, Horn,\u00a0Lower Austria), agenda, eligibility, FAQs.",
        f"- [Bootcamp 2026 (English)]({public_url('en/bootcamp.html')}): dates, agenda, eligibility, FAQs.",
        f"- [Team &\u00a0join us (Deutsch)]({public_url('team.html')}): team list and ways to volunteer or mentor.",
        f"- [Team &\u00a0join us (English)]({public_url('en/team.html')}): team list and ways to volunteer or mentor.",
        f"- [Partners (Deutsch)]({public_url('partners.html')}): supporters, school partnerships, sponsorship.",
        f"- [Partners (English)]({public_url('en/partners.html')}): supporters, school partnerships, sponsorship.",
        f"- [Events (Deutsch)]({public_url('events.html')}): upcoming and recent events.",
        f"- [Events (English)]({public_url('en/events.html')}): upcoming and recent events.",
        "",
        "## Optional",
        "",
        "- [Project Access International](https://projectaccess.org): the wider network we are part of.",
        "- [Instagram](https://www.instagram.com/projectaccess.at/): announcements and news.",
        "- Contact: austria@projectaccess.org",
        "",
    ]
    return "\n".join(sections)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete generated HTML files before building.",
    )
    args = parser.parse_args()

    if args.clean:
        print("Cleaning previously generated pages…")
        clean_outputs()

    site = load_json(CONTENT_DIR / "_site.json")
    env = build_env()

    print(f"Building {len(PAGES)} pages × {len(LANGUAGES)} languages…")
    for page_key in PAGES:
        page_content = load_json(CONTENT_DIR / f"{page_key}.json")
        for lang in LANGUAGES:
            html = render_page(env, page_key, lang, site, page_content)
            write_file(PAGES[page_key][lang], html)

    print("Writing SEO + AI discovery files…")
    write_file("sitemap.xml", render_sitemap())
    write_file("robots.txt", render_robots())
    write_file("llms.txt", render_llms_txt(site))

    print("Done.")


if __name__ == "__main__":
    main()
