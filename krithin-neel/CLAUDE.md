# CLAUDE.md — Krithin Neel Family Memories

Subproject of rsquare-studios-dashboard. Family memories page hosted on GitHub Pages.

**Last Updated:** 2026-02-19

## Overview

- **Live URL:** https://kneil31.github.io/krithin-neel/
- **GitHub Repo:** kneil31/krithin-neel (public)
- **Generator:** `generate_krithin_page.py` → `output/index.html`
- **Password:** Read from `KRITHIN_PAGE_PASSWORD` env var or `.secret` file (not hardcoded)
- **Encryption:** AES-256-GCM, 400k PBKDF2 iterations, data-driven DOM (no innerHTML)

## Design

- Warm pastel baby/family theme (cream #FFF8F0 bg, peach #E8A87C accent)
- Nunito font, photo tiles with gradient overlay (same style as rsquare-studios dashboard)
- 3 tabs: Krithin | Monika | Family
- Mobile-first (shared via WhatsApp)
- Gallery tiles: 3/4 aspect ratio, 2-column mobile, 3-column desktop
- Video tiles: 16/9 aspect ratio, always 2-column grid. Supports optional `"cover"` field for SmugMug photos
- Reel tiles: 9/16 portrait aspect ratio, 3-column grid, `<img>` tags. Supports optional `"cover"` field for SmugMug photos (much better quality than YouTube thumbs)
- Gallery tiles: Support optional `"cover"` field to override `cover_images.json` highlight images

## Data

- Image counts from `../album_stats.json` (keyed by SmugMug node_id)
- Cover images from `cover_images.json` (SmugMug highlight images, medium/large/xlarge)
- Gallery URLs, video URLs, and metadata hardcoded in generator
- Custom covers: galleries, videos, and reels all support optional `"cover"` field (SmugMug XLarge URLs)

## Content

| Tab | Galleries |
|-----|-----------|
| Krithin | Fresh 48, Cradle Ceremony, Sankranthi 2025, Temple Visit, Cake Smash, Adugulu, Halloween, New Year 2026 |
| Monika | Baby Shower, Maternity 2024, Girls Shoot 2023 |
| Family | Moniel Housewarming |

**Videos:** 6 in Krithin tab (incl. KAYU Fly High), 3 in Monika tab (all with YouTube URLs and custom SmugMug covers)
**Reels:** 13 in Krithin tab (all with SmugMug cover photos from Krithin-2026-dump album)

## Workflow

```bash
# Regenerate
cd krithin-neel
python3 generate_krithin_page.py

# Deploy to GitHub Pages
cp output/index.html /tmp/krithin-neel/
cd /tmp/krithin-neel && git add . && git commit -m "description" && git push
```

## Notes

- "Moniel Housewarming" not "Half Saree" (album name: Monika-Neel HW)
- Halloween album is "KAYU Halloween" in album_stats (node_id: K9g7f3)
- Video/reel/gallery tiles all support optional `"cover": "SmugMug URL"` field — use XLarge size for good quality
- Reel cover source album: Krithin-2026-dump (all 13 reels have custom covers)
- Gallery covers: Fresh 48 (Cg8LkMz), Cradle (zbjFvnD), Sankranthi (ZqK2JFp), Temple Visit (z5F449L), Cake Smash (qGFd3mp), Girls Shoot (NQzhzqV), Moniel HW (2vgmVNq), Baby Shower (bfcjZSM)
- Removed: Birthday 2023, Maternity 2023 (SmugMug 404), Sankranthi 2025 from Family (duplicate)
- KAYU Fly High moved from Reels to Krithin Videos; Kids Meet Teaser removed
- Skipped video: `dkpibn_N4EM` (Cradle Ceremony review only, may add later)
