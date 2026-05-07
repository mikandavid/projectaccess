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
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
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

# Maps logical page key -> per-language output path relative to ROOT.
# German pages live at the root, English pages under en/ with English slugs.
PAGES: dict[str, dict[str, str]] = {
    "index":       {"de": "index.html",     "en": "en/index.html"},
    "bootcamp":    {"de": "bootcamp.html",  "en": "en/bootcamp.html"},
    "events":      {"de": "events.html",    "en": "en/events.html"},
    "involvement": {"de": "mitmachen.html", "en": "en/get-involved.html"},
    "partners":    {"de": "partners.html",  "en": "en/partners.html"},
    "team":        {"de": "team.html",      "en": "en/team.html"},
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
    }

    if page_key == "index":
        team_data = load_json(CONTENT_DIR / "team.json")
        members_by_key = {m["key"]: m for m in team_data["members"]}
        preview_keys = page_content["team_preview"]["members_keys"]
        context["team_preview_members"] = [members_by_key[k] for k in preview_keys]

    template = env.get_template(f"{page_key}.html.j2")
    return template.render(**context)


def write_file(rel_path: str, content: str) -> None:
    out = ROOT / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(f"  wrote {rel_path}")


def clean_outputs() -> None:
    for variants in PAGES.values():
        for rel in variants.values():
            target = ROOT / rel
            if target.exists():
                target.unlink()
    en_dir = ROOT / "en"
    if en_dir.exists() and not any(en_dir.iterdir()):
        shutil.rmtree(en_dir)


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

    print("Done.")


if __name__ == "__main__":
    main()
