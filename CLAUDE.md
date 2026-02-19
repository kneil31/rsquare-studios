# CLAUDE.md — Rsquare Studios Dashboard

## IMPORTANT: Mobile-First Design

**Most users access this site on their phones via WhatsApp links.** Every change must be tested and optimized for mobile viewports first, desktop second. Always check how things look at 375px width (iPhone SE) and 390px width (iPhone 14).

## Project Overview

Notion-style dark-themed dashboard for Rsquare Studios photography business. Hosted on GitHub Pages.

- **Live URL:** https://kneil31.github.io/rsquare-studios/
- **GitHub Repo:** kneil31/rsquare-studios (public)
- **Generator:** `generate_dashboard.py` → outputs `index.html`
- **Password (internal sections):** `rsquare2026`

## 3 Sections

1. **Portfolio** (client-facing) — Category tiles with cover photos linking to SmugMug galleries
2. **Investment / Pricing** (client-facing) — Hourly rate cards with interactive quote builder
3. **Workflow Dashboard** (password-protected) — Posing guides, workflow checklists, editing reference

## Key Design Decisions

- **Mobile-first:** Bottom nav bar, floating WhatsApp button, large touch targets
- **Dark theme:** Notion-inspired (#191919 background, #8b5cf6 accent purple)
- **Cover images:** Pulled from SmugMug API (highlight images per album). Each category tile has a background photo with gradient overlay
- **Background position:** Per-category `background-position` values in `category_covers` dict (tuples of URL + position). Adjust position values when photos crop subjects poorly
- **No external dependencies:** Single self-contained HTML file, no frameworks
- **Professional copy:** "Investment" not "pricing", "images" not "pictures", "coverage" not "shooting"

## Data Sources

| Data | Source Path |
|------|-------------|
| Gallery links | `../rsqr_whatsapp_api/smugmug_galleries.json` |
| Posing guides | `../../../Upskill/Posing_Upskill/prompts/{couples,families,weddings}.md` |
| Workflow reference | `../../photo_workflow/PHOTO_WORKFLOW_CHEATSHEET.md` |
| Cover images | SmugMug API (image keys hardcoded in `category_covers` dict) |

## Cover Images (SmugMug)

Each portfolio category has a cover photo. To swap an image:

1. Get the image key from a SmugMug organize URL (e.g., `i-BvTChsc` from `https://www.smugmug.com/app/organize/.../i-BvTChsc`)
2. Fetch the image URL via SmugMug API: `GET /api/v2/image/{imageKey}!sizes`
3. Use the `X3LargeImageUrl` (1600px — good balance of quality vs load time)
4. Update the `category_covers` dict in `generate_dashboard.py`
5. Adjust the background-position tuple value if the subject gets cropped

Current covers:
| Category | Image Key | Source Album |
|----------|-----------|-------------|
| Wedding | BvTChsc | — |
| Maternity | ZqWs3n5 | — |
| Baby Shower | 3MjgbV3 | Varsha Baby Shower |
| Birthday | Xq8BHgp | — |
| Cradle | R3QTwKk | Vayu Skanda Cradle |

Homepage hero: `i-VqnMPLz` (Krishna Maternity)

Spare image (not yet used): `i-6trRsbK`

## SmugMug API Auth

- **API Key:** `nxtxC83BMVxbcJKJ8b89HLV2CBPHpSTD`
- **Config:** `~/.smugmug_config.json` (OAuth1 tokens)
- **Helper scripts:** `fetch_cover_images.py`, `fetch_smugmug_sizes.py`

## Workflow

```bash
# Regenerate after changes
python3 generate_dashboard.py

# Push to GitHub Pages
git add index.html generate_dashboard.py
git commit -m "description"
git push

# Cache busting — tell user to add ?v=N or use incognito
```

## Pricing (Hardcoded in generator)

- Solo Photography: $150/hr
- Solo Photo + Video: $235/hr
- Dual Coverage (Photo + Video): $325/hr
- All packages include: edited images, cinematic teaser, SmugMug gallery, lifetime cloud storage

## Mobile-Specific Notes

- Bottom nav bar with 5 tabs (Home, Portfolio, Pricing, Book, Contact)
- Floating WhatsApp button (bottom-right, above nav bar)
- Category tiles use 2-column grid on mobile
- `safe-area-inset-bottom` for iPhone notch/home indicator
- Hero image uses XLarge (1024px) on mobile, X3Large (1600px) on desktop
- Test every layout change at 375px width minimum
