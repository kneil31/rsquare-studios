# CLAUDE.md — Rsquare Studios Dashboard

## IMPORTANT: Mobile-First Design

**Most users access this site on their phones via WhatsApp links.** Every change must be tested and optimized for mobile viewports first, desktop second. Always check how things look at 375px width (iPhone SE) and 390px width (iPhone 14).

## Project Overview

Notion-style dark-themed dashboard for Rsquare Studios photography business. Hosted on GitHub Pages.

- **Live URL:** https://kneil31.github.io/rsquare-studios/
- **GitHub Repo:** kneil31/rsquare-studios (public)
- **Generator:** `generate_dashboard.py` → outputs `index.html`
- **Client password:** `rsquare2026` (unlocks pricing, booking, quote builder)
- **Internal password:** `r2workflow` (unlocks workflow, checklists, posing guides, editing projects)

## 3 Sections

1. **Portfolio** (client-facing) — Category tiles with cover photos linking to SmugMug galleries
2. **Investment / Pricing** (client-facing) — Hourly rate cards with interactive quote builder
3. **Workflow Dashboard** (password-protected) — Posing guides, workflow checklists, editing reference, editing project tracker

## Key Design Decisions

- **Mobile-first:** Bottom nav bar, floating WhatsApp button, large touch targets
- **Dark theme:** Notion-inspired (#191919 background, #8b5cf6 accent purple)
- **Hero layout:** Option D split (image left, text right) with CSS `mask-image` blend — photo dissolves into a purple-to-black gradient (`#2d1854` → `#0e0518` → `#050208`). On mobile, stacks vertically with bottom-fade blend.
- **Hero stats:** 300+ Galleries, 5+ Years, 50+ Weddings (real numbers from SmugMug + Ram)
- **Hero image:** `hero.jpg` — purple silhouette wedding photo (145KB, 1600px wide)
- **Two-level AES-256-GCM encryption:** Client sections (pricing, booking, `__config__`) and internal sections (workflow, checklists, posing guides) encrypted with separate passwords. No plaintext in HTML source.
- **Cover images:** Pulled from SmugMug API (highlight images per album). Each category tile has a background photo
- **Tile labels below image:** Category name and gallery count are displayed below the tile image (not overlaid on top), to avoid clashing with text in photos
- **Background position:** Per-category `background-position` values in `category_covers` dict (tuples of URL + position). Adjust position values when photos crop subjects poorly
- **No external dependencies:** Single self-contained HTML file, no frameworks
- **Professional copy:** "Investment" not "pricing", "images" not "pictures", "coverage" not "shooting"

## My Gear Section

- **Inline expandable section** on the home page — replaces the old kit.co external link
- **Data:** `GEAR_LIST` dict in `generate_dashboard.py` — 7 categories rendered at build time
- **Layout:** Collapsed by default, click to expand. 2-col grid (mobile) / 3-col (desktop)
- **Categories:** Camera Bodies, Lenses, Lighting, Light Modifiers, Stabilization & Drone, Monitors, Accessories
- **To update gear:** Edit the `GEAR_LIST` dict, then regenerate

## Data Sources

| Data | Source Path |
|------|-------------|
| Gallery links | `../rsqr_whatsapp_api/smugmug_galleries.json` |
| Posing guides | `../../../Upskill/Posing_Upskill/prompts/{couples,families,weddings}.md` |
| Workflow reference | `../../photo_workflow/PHOTO_WORKFLOW_CHEATSHEET.md` |
| Cover images | SmugMug API (image keys hardcoded in `category_covers` dict) |
| Editing projects | `editing_projects.json` (local, not pushed to GitHub) |
| Gear list | `GEAR_LIST` dict in `generate_dashboard.py` |

## Cover Images (SmugMug)

Each portfolio category has a cover photo. To swap an image:

1. Get the image key from a SmugMug organize URL (e.g., `i-BvTChsc` from `https://www.smugmug.com/app/organize/.../i-BvTChsc`)
2. Fetch the image URL via SmugMug API: `GET /api/v2/image/{imageKey}!sizes`
3. Use the `X3LargeImageUrl` (1600px — good balance of quality vs load time)
4. Update the `category_covers` dict in `generate_dashboard.py`
5. Adjust the background-position tuple value if the subject gets cropped

Current covers (all 9 categories have tuned `background-position`):
| Category | Image Key | Position |
|----------|-----------|----------|
| Wedding | BvTChsc | center 43% |
| Engagement | 8NfsLKT | 38% 47% |
| Pre-Wedding | GfR24FT | center 24% |
| Half Saree | MCmGphP | 68% 52% |
| Maternity | ZqWs3n5 | center 18% |
| Baby Shower | 3MjgbV3 | 37% 18% |
| Birthday | Xq8BHgp | center 40% |
| Cradle | R3QTwKk | center 47% |
| Celebrations | J8zjNdj | 38% 30% |

Homepage hero: `hero.jpg` — purple silhouette wedding photo (local file, not SmugMug). Option D split layout with CSS mask blend.

Spare image (not yet used): `i-6trRsbK`

## SmugMug API Auth

- **API Key:** `nxtxC83BMVxbcJKJ8b89HLV2CBPHpSTD`
- **Config:** `~/.smugmug_config.json` (OAuth1 tokens)
- **Helper scripts:** `fetch_cover_images.py`, `fetch_smugmug_sizes.py`, `fetch_album_stats.py`, `detect_cover_faces.py`

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

## Pricing (AES-encrypted in output)

- Solo Photography: $150/hr
- Solo Photo + Video: $235/hr
- Dual Coverage (Photo + Video): $325/hr
- All packages include: edited images, cinematic teaser, SmugMug gallery, lifetime cloud storage
- **Rate amounts are inside the encrypted `__config__` blob** — not visible in HTML source or JS
- Dropdown uses stable IDs (`photo_only`, `photo_video`, `dual_coverage`) instead of display strings

## Security

- **Two-level AES-256-GCM** encryption at build time (Python `cryptography` package)
  - `ENCRYPTED_CLIENT` blob: pricing, booking, `__config__` (rates) — password `rsquare2026`
  - `ENCRYPTED_INTERNAL` blob: workflow, checklists, posing guides, editing projects — password `r2workflow`
- **Web Crypto API** decryption at runtime (PBKDF2, 400k iterations, SHA-256)
- Random 16-byte salt + 12-byte IV per build (`os.urandom`)
- No sessionStorage/localStorage — decrypted content is memory-only (`_appConfig`)
- **Schema versioned** encrypted payloads (`"v": 1`)
- 3-strike lockout with 15s cooldown on wrong password
- **Password toggle** (show/hide eye icon) + password hint
- **Logout button** (visible when unlocked, clears decrypted content + reloads)
- **"Don't share" reminder** on password gate
- **Quote builder:** DOM-based construction (no innerHTML with user input — XSS safe)
- **Privacy:** `<meta name="robots" content="noindex, nofollow, noarchive">`
- Git history cleaned with `filter-repo` — no plaintext in old commits
- Client password cannot decrypt internal sections (verified via cross-test)

## Editing Project Tracker

- **Data:** `editing_projects.json` (local only — delivery links are sensitive)
- **Dashboard:** "Editing Projects" section behind `r2workflow`, shows table with status badges
- **Status auto-detection:** SENT (blue), OVERDUE (red, >14 days), COMPLETED (green)
- **Daily reminder:** `editing_reminder.py` runs at 10 AM via `com.rsquare.editing-reminder.plist`
- **WhatsApp follow-up:** "Follow Up" button opens wa.me link with pre-filled message to editor
- **To enable WhatsApp:** Add `editor` name and `editor_phone` (country code + number) in JSON
- **To update projects:** Edit `editing_projects.json`, then `python3 generate_dashboard.py`

## Subprojects

- **krithin-neel/** — Separate page generator (`generate_krithin_page.py`) with its own cover images and output

## Mobile-Specific Notes

- Bottom nav bar with 5 tabs (Home, Portfolio, Pricing, Book, Contact)
- Floating WhatsApp button (bottom-right, above nav bar)
- Category tiles use 2-column grid on mobile
- `safe-area-inset-bottom` for iPhone notch/home indicator
- Hero: split layout on desktop (image left 50%, text right), stacks vertically on mobile
- Hero image uses CSS `mask-image` to blend into background gradient (no hard edge)
- Test every layout change at 375px width minimum
