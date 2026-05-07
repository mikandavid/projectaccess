# Project Access Austria Site Plan

## Goal

Create a fast, static, responsive website for Project Access Austria that feels aligned with the redesigned Project Access International website while keeping the Austrian team, bootcamp, school outreach, sponsor, and legal content visible.

The first draft is a one-page site because it is easier to launch, easier to maintain, and gives every audience a clear route. The content architecture below can later become separate pages if the team wants more depth.

## Recommended Pages

### Launch MVP

1. `index.html`
   - Hero
   - Impact numbers
   - Programme overview
   - Bootcamp 2026
   - Ways to get involved
   - Team
   - Events/news
   - Contact and legal footer

### Future Split

1. `programme.html`
   - Mentoring, resources, preparation/follow-up course, community.
   - Link to international Project Access programme.

2. `bootcamp.html`
   - Full bootcamp details, dates, eligibility, FAQs, gallery, application link.

3. `schools.html`
   - School partnership offer, benefits, registration, materials.

4. `partners.html`
   - Sponsor offer, partner types, quote, contact CTA.

5. `team.html`
   - Full team grid, roles, recruiting CTA.

## One-Page Layout

### 1. Navigation

Sticky, light navigation with:
- Programme
- Bootcamp
- Engagement
- Team
- Kontakt

Primary CTA:
- Kostenlos mitmachen

### 2. Hero

Purpose:
- Say immediately who PA Austria helps.
- Connect local Austria/South Tyrol focus to the global Project Access mission.

Content:
- Eyebrow: Project Access Austria
- Heading: "Top-Unis sollen nicht vom Hintergrund abhängen."
- Body: Free mentoring and bootcamp support for students from Austria and South Tyrol.
- CTAs: "Als Student:in starten", "Mentor:in werden"
- Visual: Bootcamp image with a small stat badge.

### 3. Impact

Four cards:
- 185 Jugendliche mit Mentor:innen
- 120 Bootcamp-Teilnehmende
- 77-84% Offers von Top-3-Unis
- 139 aktive Mentor:innen

### 4. International Context

Short section linking PA Austria to Project Access International:
- free, one-to-one mentorship
- global community
- resources and webinars
- mentors at top universities in UK, US, and EU

### 5. Programme

Four feature cards:
- 1:1 Mentoring
- Bewerbungs-Bootcamp
- Vorbereitung & Ressourcen
- Community & Netzwerk

### 6. Bootcamp

High-emphasis section:
- date, location, cost
- who it is for
- what students work on
- CTA to sign up / follow Instagram for updates

### 7. Get Involved

Four audience cards:
- Schüler:innen & Studierende
- Mentor:innen
- Schulen
- Sponsor:innen & Partner

Each card should explain the benefit and include an action link.

### 8. Team

Compact grid of current PA Austria team members. Show name, role, university. Use headshots from the legacy site where available.

### 9. Events and Press

Include:
- BeSt-Messe 2026, Messe Wien, Stand A37
- Bootcamp 2025 retrospective
- press links from the legacy site

### 10. Contact and Footer

Include:
- austria@projectaccess.org
- @projectaccess.at
- Project Access Austria legal name, Vienna association, address, ZVR number.

## Visual Direction

Use a restrained but lively style:
- Background: warm cream and soft peach.
- Text: dark navy/ink.
- Accents: orange, yellow, coral, and muted green/teal.
- Large editorial headings, rounded cards, pill labels, gentle shadows.
- Human photography as organic rounded shapes.
- Avoid over-animation or heavy decoration.

## Responsive Requirements

The first draft should support:
- Fluid type using `clamp()`.
- Mobile-first grid layouts.
- Navigation wrapping on small screens.
- Large tap targets for CTAs.
- Team cards that collapse from 4 columns to 2 and then 1.
- Images with fixed aspect ratios and `object-fit: cover`.
- No JavaScript dependency.

## Draft File Structure

```text
.
├── index.html
├── styles.css
└── docs
    ├── content-inventory.md
    └── site-plan.md
```
