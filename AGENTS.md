# Project Access Austria Website Guide

## Who We Are

Project Access Austria is the Austrian chapter of Project Access. The site serves students from Austria and South Tyrol who are interested in applying to selective international universities, especially through free mentoring, application resources, and the annual bootcamp.

The Austrian organization is legally represented as Projekt Hochschulzugang, an association based in Vienna. Keep the tone student-centered, encouraging, practical, and connected to the wider Project Access mission of making top universities more accessible regardless of background.

## Relevant Links

- Live deployment: https://projectaccess.at
- GitHub repository: https://github.com/mikandavid/projectaccess
- Project Access International: https://projectaccess.org
- Instagram: https://www.instagram.com/projectaccess.at/
- Contact: austria@projectaccess.org

## Stack

- Static bilingual website for Project Access Austria.
- Source content lives in JSON files under `content/`.
- Page structure is defined with Jinja2 templates under `templates/`.
- `build.py` renders German pages at the repository root and English pages under `en/`.
- Styling is in the single global stylesheet `styles.css`.
- Runtime JavaScript is limited to the external Calendly badge loaded from `templates/base.html.j2`.
- Python dependency: `Jinja2`, installed from `requirements.txt`.

## Build

Run:

```bash
python3 -m pip install -r requirements.txt
python3 build.py
```

Use `python3 build.py --clean` to remove generated HTML pages before rebuilding.

Generated HTML files include:

- German: `index.html`, `bootcamp.html`, `events.html`, `mitmachen.html`, `partners.html`, `team.html`
- English: `en/index.html`, `en/bootcamp.html`, `en/events.html`, `en/get-involved.html`, `en/partners.html`, `en/team.html`

Prefer editing the JSON content, Jinja templates, or `styles.css`; rebuild generated HTML after source changes.

## Source Layout

- `build.py`: build pipeline, page map, language handling, localized anchors, template helpers, and output paths.
- `content/_site.json`: shared site chrome, navigation, footer, language switch labels, Calendly badge settings, and press links.
- `content/<page>.json`: bilingual page content for each logical page.
- `templates/base.html.j2`: shared HTML shell, metadata, font/css includes, header/footer includes, and Calendly script.
- `templates/_partials/`: reusable template fragments such as header, footer, and press sections.
- `templates/<page>.html.j2`: page-specific layouts.
- `styles.css`: global visual system, layout, responsive rules, and components.
- `CNAME`: custom domain for the live deployment.
- `.nojekyll`: keeps the static deployment compatible with GitHub Pages-style hosting.
- `docs/`: planning and source-content notes. Treat these as reference material, not generated output.

## Website Layout

The site is bilingual with German as the root-language output and English in `en/`.

Primary pages:

- Home: overview of mission, programme, bootcamp, involvement paths, team preview, events, and contact.
- Bootcamp: details for the application bootcamp, eligibility, activities, and calls to action.
- Events: events/news and related press context.
- Involvement: audience paths for students, mentors, schools, and partners.
- Partners: sponsor and partner information.
- Team: full team/member presentation.

Shared navigation is generated from `content/_site.json`. The header includes a CSS-only responsive menu toggle, language links, and optional page-level CTA from content.

## Design Notes

- Visual direction: warm cream/peach backgrounds, dark ink text, orange/yellow/coral/green accents, rounded cards, pill labels, gentle shadows, and human photography.
- Typography uses Inter from Google Fonts via `templates/base.html.j2`.
- Layout should stay responsive with fluid type, mobile-first grids, large tap targets, and images using fixed aspect ratios plus `object-fit: cover`.
- Avoid adding heavy animation or new frontend dependencies unless explicitly requested.

## Editing Guidance

- Keep content bilingual. Most user-facing strings should be represented in both `de` and `en` fields.
- If adding a page, update `PAGES` in `build.py`, add `content/<page>.json`, add `templates/<page>.html.j2`, and add navigation in `content/_site.json` if it belongs in the header.
- Use `page_href(...)`, `asset(...)`, `anchor(...)`, and `t(...)` helpers in templates instead of hardcoding cross-language URLs.
- Keep generated HTML consistent by rebuilding after source edits.
- Do not edit `.venv/` or generated dependency files.
