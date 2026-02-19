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
- **Hero layout:** Option D split (image left, text right) with CSS `mask-image` blend — photo dissolves into a purple-to-black gradient (`#2d1854` → `#0e0518` → `#050208`). On mobile, stacks vertically with bottom-fade blend.
- **Hero stats:** 300+ Galleries, 5+ Years, 50+ Weddings (real numbers from SmugMug + Ram)
- **Hero image:** `hero.jpg` — purple silhouette wedding photo (145KB, 1600px wide)
- **AES-256-GCM encryption:** Protected sections (pricing, booking, workflow, posing guides) are encrypted at build time. No plaintext in HTML source. Rate amounts stored in encrypted `__config__` key.
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

Homepage hero: `hero.jpg` — purple silhouette wedding photo (local file, not SmugMug). Option D split layout with CSS mask blend.

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

## Pricing (AES-encrypted in output)

- Solo Photography: $150/hr
- Solo Photo + Video: $235/hr
- Dual Coverage (Photo + Video): $325/hr
- All packages include: edited images, cinematic teaser, SmugMug gallery, lifetime cloud storage
- **Rate amounts are inside the encrypted `__config__` blob** — not visible in HTML source or JS
- Dropdown uses stable IDs (`photo_only`, `photo_video`, `dual_coverage`) instead of display strings

## Security

- **AES-256-GCM** encryption at build time (Python `cryptography` package)
- **Web Crypto API** decryption at runtime (PBKDF2, 100k iterations, SHA-256)
- Random 16-byte salt + 12-byte IV per build (`os.urandom`)
- No sessionStorage/localStorage — decrypted content is memory-only (`_decryptedPages`, `_appConfig`)
- 3-strike lockout with 15s cooldown on wrong password
- Password hint shown below input
- Git history cleaned with `filter-repo` — no plaintext in old commits

## Mobile-Specific Notes

- Bottom nav bar with 5 tabs (Home, Portfolio, Pricing, Book, Contact)
- Floating WhatsApp button (bottom-right, above nav bar)
- Category tiles use 2-column grid on mobile
- `safe-area-inset-bottom` for iPhone notch/home indicator
- Hero: split layout on desktop (image left 50%, text right), stacks vertically on mobile
- Hero image uses CSS `mask-image` to blend into background gradient (no hard edge)
- Test every layout change at 375px width minimum
